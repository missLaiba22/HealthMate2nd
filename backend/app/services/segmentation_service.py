import os
import logging
from typing import Optional

import numpy as np
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Ensure environment variables from .env are available even if service is imported directly

load_dotenv()

class SegmentationService:
    """
    Loads a Keras .h5 segmentation model lazily and runs inference.
    The model path is taken from SEGMENTATION_MODEL_PATH or a default location.
    """

    def __init__(self, model_path: Optional[str] = None):
        self._model = None
        # Resolve default path relative to this file, not CWD
        default_path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),  # .../backend/app/services
                "..",                      # .../backend/app
                "models",
                "weights",
                "brain_tumor_model.h5",
            )
        )
        env_path = os.getenv("SEGMENTATION_MODEL_PATH")
        self._model_path = os.path.abspath(model_path or env_path or default_path)
        logger.info(f"Segmentation model path set to: {self._model_path}")

    def _ensure_model_loaded(self):
        if self._model is None:
            try:
                # Import tensorflow/keras only when needed
                from tensorflow import keras

                if not os.path.exists(self._model_path):
                    raise FileNotFoundError(
                        f"Segmentation model not found at: {self._model_path}"
                    )
                logger.info(f"Loading segmentation model from {self._model_path} ...")
                # Avoid needing training-time custom losses/metrics
                self._model = keras.models.load_model(self._model_path, compile=False)
                logger.info("Segmentation model loaded successfully")
            except Exception as exc:
                logger.error(f"Failed to load segmentation model: {exc}")
                raise

    def predict_mask(self, image_array: np.ndarray) -> np.ndarray:
        """
        Runs model inference and returns a binary/soft mask.

        The caller is responsible for preparing the image_array to match
        the model's expected input size and normalization.
        """
        self._ensure_model_loaded()

        if image_array is None:
            raise ValueError("image_array must not be None")

        # Ensure batch dimension
        if image_array.ndim == 3:
            image_array = np.expand_dims(image_array, axis=0)

        preds = self._model.predict(image_array)
        return preds

    def predict_from_modalities(self, flair_image: np.ndarray, t1ce_image: np.ndarray) -> np.ndarray:
        """
        Accepts two 2D arrays (grayscale) for FLAIR and T1CE, resizes and stacks
        into a (1, 128, 128, 2) tensor normalized to [0,1], and returns softmax
        logits of shape (1, 128, 128, 4).
        """
        from PIL import Image

        if flair_image is None or t1ce_image is None:
            raise ValueError("Both flair_image and t1ce_image are required")

        self._ensure_model_loaded()

        # Ensure PIL Images for resizing then back to numpy
        if isinstance(flair_image, np.ndarray):
            flair_pil = Image.fromarray(
                (flair_image * 255).astype(np.uint8) if flair_image.dtype != np.uint8 else flair_image
            ).convert("L")
        else:
            flair_pil = flair_image.convert("L")

        if isinstance(t1ce_image, np.ndarray):
            t1ce_pil = Image.fromarray(
                (t1ce_image * 255).astype(np.uint8) if t1ce_image.dtype != np.uint8 else t1ce_image
            ).convert("L")
        else:
            t1ce_pil = t1ce_image.convert("L")

        flair_resized = flair_pil.resize((128, 128))
        t1ce_resized = t1ce_pil.resize((128, 128))

        flair_np = np.array(flair_resized, dtype=np.float32) / 255.0
        t1ce_np = np.array(t1ce_resized, dtype=np.float32) / 255.0

        stacked = np.stack([flair_np, t1ce_np], axis=-1)  # (128,128,2)
        batched = np.expand_dims(stacked, axis=0)  # (1,128,128,2)

        preds = self._model.predict(batched)
        return preds

    async def segment_image(self, image_data: str) -> dict:
        """
        High-level method for single image segmentation.
        This method handles the complete workflow from base64 image to segmentation result.
        """
        try:
            import base64
            from PIL import Image
            import io
            
            # Decode base64 image
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to numpy array
            if image.mode != 'L':
                image = image.convert('L')
            image_array = np.array(image, dtype=np.float32)
            
            # Normalize if needed
            if image_array.max() > 1.0:
                image_array = image_array / 255.0
            
            # Get segmentation prediction
            prediction = self.predict_mask(image_array)
            
            # Process prediction to get binary mask
            if prediction.ndim == 4:  # (batch, height, width, channels)
                mask = prediction[0]  # Remove batch dimension
            else:
                mask = prediction
            
            # Convert to binary mask (threshold at 0.5)
            binary_mask = (mask > 0.5).astype(np.uint8)
            
            # Calculate statistics
            total_pixels = binary_mask.size
            segmented_pixels = np.sum(binary_mask)
            segmentation_percentage = (segmented_pixels / total_pixels) * 100
            
            # Convert mask back to base64 for response
            mask_image = Image.fromarray((binary_mask * 255).astype(np.uint8))
            buffer = io.BytesIO()
            mask_image.save(buffer, format='PNG')
            mask_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            return {
                "success": True,
                "segmentation_mask": mask_base64,
                "statistics": {
                    "total_pixels": int(total_pixels),
                    "segmented_pixels": int(segmented_pixels),
                    "segmentation_percentage": float(segmentation_percentage)
                },
                "message": "Image segmentation completed successfully"
            }
            
        except Exception as e:
            logger.error(f"Error in image segmentation: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to segment image"
            }

    async def segment_dual_modality(self, flair_image: str, t1ce_image: str) -> dict:
        """
        High-level method for dual modality brain segmentation.
        This method handles the complete workflow from base64 images to segmentation result.
        """
        try:
            import base64
            from PIL import Image
            import io
            
            # Decode FLAIR image
            flair_bytes = base64.b64decode(flair_image)
            flair_pil = Image.open(io.BytesIO(flair_bytes))
            if flair_pil.mode != 'L':
                flair_pil = flair_pil.convert('L')
            flair_array = np.array(flair_pil, dtype=np.float32)
            if flair_array.max() > 1.0:
                flair_array = flair_array / 255.0
            
            # Decode T1CE image
            t1ce_bytes = base64.b64decode(t1ce_image)
            t1ce_pil = Image.open(io.BytesIO(t1ce_bytes))
            if t1ce_pil.mode != 'L':
                t1ce_pil = t1ce_pil.convert('L')
            t1ce_array = np.array(t1ce_pil, dtype=np.float32)
            if t1ce_array.max() > 1.0:
                t1ce_array = t1ce_array / 255.0
            
            # Get segmentation prediction
            prediction = self.predict_from_modalities(flair_array, t1ce_array)
            
            # Process prediction (assuming 4-class segmentation: background, necrotic core, edema, enhancing tumor)
            if prediction.ndim == 4:  # (batch, height, width, classes)
                pred = prediction[0]  # Remove batch dimension
            else:
                pred = prediction
            
            # Get class predictions
            class_predictions = np.argmax(pred, axis=-1)
            
            # Calculate statistics for each class
            total_pixels = class_predictions.size
            class_stats = {}
            class_names = ['Background', 'Necrotic Core', 'Edema', 'Enhancing Tumor']
            
            for i, class_name in enumerate(class_names):
                class_pixels = int(np.sum(class_predictions == i))  # Convert to Python int
                percentage = float((class_pixels / total_pixels) * 100)  # Convert to Python float
                class_stats[class_name.lower().replace(' ', '_')] = {
                    "pixels": class_pixels,
                    "percentage": percentage
                }
            
            # Convert prediction to RGB visualization
            colors = np.array([
                [0, 0, 0],        # Background - Black
                [255, 0, 0],      # Necrotic Core - Red
                [0, 255, 0],      # Edema - Green
                [0, 0, 255]       # Enhancing Tumor - Blue
            ])
            
            rgb_prediction = colors[class_predictions]
            pred_image = Image.fromarray(rgb_prediction.astype(np.uint8))
            buffer = io.BytesIO()
            pred_image.save(buffer, format='PNG')
            pred_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            # Generate insights and recommendations
            insights = []
            recommendations = []
            
            # Extract pixel counts from class_stats
            necrotic_pixels = class_stats.get('necrotic_core', {}).get('pixels', 0)
            edema_pixels = class_stats.get('edema', {}).get('pixels', 0)
            enhancing_pixels = class_stats.get('enhancing_tumor', {}).get('pixels', 0)
            
            # Calculate volumes (assuming 1mm³ per pixel for simplicity)
            pixel_to_volume_ratio = 1.0  # mm³ per pixel
            necrotic_volume = (necrotic_pixels * pixel_to_volume_ratio) / 1000.0  # cm³
            edema_volume = (edema_pixels * pixel_to_volume_ratio) / 1000.0  # cm³
            enhancing_volume = (enhancing_pixels * pixel_to_volume_ratio) / 1000.0  # cm³
            total_tumor_volume = necrotic_volume + enhancing_volume
            
            # Generate insights based only on percentages and ratios (no duplicate volumes)
            if total_tumor_volume > 0.0 and total_pixels > 0:
                total_brain_volume = (total_pixels * pixel_to_volume_ratio) / 1000.0
                tumor_percentage = (total_tumor_volume / total_brain_volume) * 100
                insights.append(f"Tumor occupies {tumor_percentage:.1f}% of total brain volume")
                
                # Add tumor composition analysis
                if enhancing_volume > 0.0 and necrotic_volume > 0.0:
                    enhancing_ratio = (enhancing_volume / total_tumor_volume) * 100
                    necrotic_ratio = (necrotic_volume / total_tumor_volume) * 100
                    insights.append(f"Tumor composition: {enhancing_ratio:.1f}% enhancing, {necrotic_ratio:.1f}% necrotic")
            else:
                insights.append("No tumor detected in the segmentation")
            
            # Generate recommendations
            recommendations.append("Consult with neurosurgeon for treatment planning")
            recommendations.append("Consider follow-up MRI in 4-6 weeks")
            
            if edema_volume > 0.0:
                recommendations.append("Consider steroid therapy for edema management")
            
            recommendations.append("Monitor for neurological symptoms")
            recommendations.append("Review with radiologist for detailed analysis")
            
            return {
                "success": True,
                "segmentation_result": pred_base64,
                "class_statistics": class_stats,
                "total_pixels": int(total_pixels),
                "insights": insights,
                "recommendations": recommendations,
                "message": "Dual modality brain segmentation completed successfully"
            }
            
        except Exception as e:
            logger.error(f"Error in dual modality segmentation: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to segment dual modality brain scan"
            }


# Singleton instance for reuse
segmentation_service = SegmentationService()


