import os
import logging
from typing import Optional
import numpy as np
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Ensure environment variables from .env are available
load_dotenv()

class BreastSegmentationService:
    """
    Loads a Keras .h5 segmentation model for breast ultrasound analysis.
    The model path is taken from BREAST_SEGMENTATION_MODEL_PATH or a default location.
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
                "breast_segmentation_model.h5",
            )
        )
        env_path = os.getenv("BREAST_SEGMENTATION_MODEL_PATH")
        self._model_path = os.path.abspath(model_path or env_path or default_path)
        logger.info(f"Breast segmentation model path set to: {self._model_path}")

    def _ensure_model_loaded(self):
        if self._model is None:
            try:
                # Import tensorflow/keras only when needed
                from tensorflow import keras

                if not os.path.exists(self._model_path):
                    raise FileNotFoundError(
                        f"Breast segmentation model not found at: {self._model_path}"
                    )
                logger.info(f"Loading breast segmentation model from {self._model_path} ...")
                # Load model with custom objects to handle version compatibility
                try:
                    # Create a custom Conv2DTranspose that ignores unsupported parameters
                    try:
                        from tensorflow.keras.layers import Conv2DTranspose
                    except ImportError:
                        from keras.layers import Conv2DTranspose
                    
                    class CompatibleConv2DTranspose(Conv2DTranspose):
                        def __init__(self, *args, **kwargs):
                            # Remove unsupported parameters for older TensorFlow versions
                            kwargs.pop('groups', None)
                            kwargs.pop('output_padding', None)
                            super().__init__(*args, **kwargs)
                    
                    custom_objects = {
                        'Conv2DTranspose': CompatibleConv2DTranspose
                    }
                    
                    self._model = keras.models.load_model(
                        self._model_path, 
                        compile=False, 
                        custom_objects=custom_objects
                    )
                    logger.info("Breast segmentation model loaded successfully with custom objects")
                except Exception as e:
                    logger.warning(f"Custom objects loading failed: {e}")
                    # Try loading with safe_mode=False for newer TensorFlow versions
                    try:
                        self._model = keras.models.load_model(
                            self._model_path, 
                            compile=False,
                            safe_mode=False
                        )
                        logger.info("Breast segmentation model loaded successfully with safe_mode=False")
                    except Exception as e2:
                        logger.warning(f"Safe mode loading failed: {e2}")
                        # Try standard loading as last resort
                        try:
                            self._model = keras.models.load_model(self._model_path, compile=False)
                            logger.info("Breast segmentation model loaded successfully with standard method")
                        except Exception as e3:
                            logger.error(f"All loading methods failed: {e3}")
                            raise e3
            except Exception as exc:
                logger.error(f"Failed to load breast segmentation model: {exc}")
                raise

    def predict_mask(self, image_array: np.ndarray) -> np.ndarray:
        """
        Runs model inference and returns a binary mask for breast ultrasound.
        
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

    def predict_from_ultrasound(self, ultrasound_image: np.ndarray) -> np.ndarray:
        """
        Accepts a 2D array (grayscale) for breast ultrasound, resizes and normalizes
        to [0,1], and returns binary segmentation mask.
        """
        from PIL import Image

        if ultrasound_image is None:
            raise ValueError("ultrasound_image is required")

        self._ensure_model_loaded()

        # Handle different input types
        if isinstance(ultrasound_image, np.ndarray):
            # If already a numpy array, use it directly
            if ultrasound_image.ndim == 2:  # (height, width)
                ultrasound_np = ultrasound_image.astype(np.float32)
            elif ultrasound_image.ndim == 3:  # (height, width, channels)
                # Convert to grayscale if needed
                if ultrasound_image.shape[2] == 3:
                    # Convert RGB to grayscale
                    ultrasound_np = np.dot(ultrasound_image[...,:3], [0.2989, 0.5870, 0.1140]).astype(np.float32)
                else:
                    ultrasound_np = ultrasound_image[:,:,0].astype(np.float32)
            else:
                raise ValueError(f"Unsupported image dimensions: {ultrasound_image.shape}")
            
            # Normalize to [0,1] if not already
            if ultrasound_np.max() > 1.0:
                ultrasound_np = ultrasound_np / 255.0
                
            # Resize if needed
            if ultrasound_np.shape != (128, 128):
                ultrasound_pil = Image.fromarray((ultrasound_np * 255).astype(np.uint8)).convert("L")
                ultrasound_resized = ultrasound_pil.resize((128, 128))
                ultrasound_np = np.array(ultrasound_resized, dtype=np.float32) / 255.0
        else:
            # Handle PIL Image
            ultrasound_pil = ultrasound_image.convert("L")
            ultrasound_resized = ultrasound_pil.resize((128, 128))
            ultrasound_np = np.array(ultrasound_resized, dtype=np.float32) / 255.0

        # Check model input shape to determine correct dimensions
        model_input_shape = self._model.input_shape
        logger.info(f"Model input shape: {model_input_shape}")
        logger.info(f"Processed image shape: {ultrasound_np.shape}")
        
        # Prepare input based on model expectations
        if len(model_input_shape) == 4:  # (batch, height, width, channels)
            # Add channel dimension and batch dimension
            ultrasound_batched = np.expand_dims(ultrasound_np, axis=0)  # (1, 128, 128)
            ultrasound_batched = np.expand_dims(ultrasound_batched, axis=-1)  # (1, 128, 128, 1)
        elif len(model_input_shape) == 3:  # (batch, height, width)
            # Add only batch dimension
            ultrasound_batched = np.expand_dims(ultrasound_np, axis=0)  # (1, 128, 128)
        else:
            # Default to 4D input
            ultrasound_batched = np.expand_dims(ultrasound_np, axis=0)  # (1, 128, 128)
            ultrasound_batched = np.expand_dims(ultrasound_batched, axis=-1)  # (1, 128, 128, 1)

        logger.info(f"Final input shape for prediction: {ultrasound_batched.shape}")
        preds = self._model.predict(ultrasound_batched)
        logger.info(f"Model prediction shape: {preds.shape}")
        logger.info(f"Model prediction dtype: {preds.dtype}")
        return preds

    async def segment_breast_ultrasound(self, image_data: str) -> dict:
        """
        High-level method for breast ultrasound segmentation.
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
            prediction = self.predict_from_ultrasound(image_array)
            
            # Process prediction to get binary mask
            logger.info(f"Prediction shape: {prediction.shape}")
            logger.info(f"Prediction dtype: {prediction.dtype}")
            
            # Handle different prediction output shapes
            if prediction.ndim == 4:  # (batch, height, width, channels)
                mask = prediction[0]  # Remove batch dimension
            elif prediction.ndim == 3:  # (batch, height, width)
                mask = prediction[0]  # Remove batch dimension
            else:
                mask = prediction
            
            # Ensure mask is 2D
            if mask.ndim == 3:
                # If still 3D, take the first channel or squeeze
                if mask.shape[-1] == 1:
                    mask = mask.squeeze(-1)
                else:
                    mask = mask[:, :, 0]
            
            # Convert to binary mask (threshold at 0.5)
            binary_mask = (mask > 0.5).astype(np.uint8)
            
            logger.info(f"Final binary mask shape: {binary_mask.shape}")
            logger.info(f"Binary mask dtype: {binary_mask.dtype}")
            
            # Calculate statistics
            total_pixels = binary_mask.size
            segmented_pixels = np.sum(binary_mask)
            segmentation_percentage = (segmented_pixels / total_pixels) * 100
            
            # Convert mask back to base64 for response with red overlay
            try:
                # Ensure the mask is the right shape and type for PIL
                if binary_mask.ndim != 2:
                    logger.error(f"Binary mask has wrong dimensions: {binary_mask.shape}")
                    raise ValueError(f"Expected 2D mask, got {binary_mask.ndim}D")
                
                # Create red overlay for lesions
                if segmented_pixels > 0:
                    # Create RGB image with red lesions
                    red_overlay = np.zeros((binary_mask.shape[0], binary_mask.shape[1], 3), dtype=np.uint8)
                    red_overlay[:, :, 0] = binary_mask * 255  # Red channel for lesions
                    # Keep green and blue channels at 0 for pure red
                    
                    mask_image = Image.fromarray(red_overlay, mode='RGB')
                    logger.info(f"Creating red overlay image from mask shape: {red_overlay.shape}")
                else:
                    # No lesions detected, return black image
                    black_image = np.zeros((binary_mask.shape[0], binary_mask.shape[1], 3), dtype=np.uint8)
                    mask_image = Image.fromarray(black_image, mode='RGB')
                    logger.info("No lesions detected, returning black overlay")
                
                buffer = io.BytesIO()
                mask_image.save(buffer, format='PNG')
                mask_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                
            except Exception as e:
                logger.error(f"Error creating mask image: {str(e)}")
                # Return a simple black mask as fallback
                fallback_mask = np.zeros((128, 128, 3), dtype=np.uint8)
                mask_image = Image.fromarray(fallback_mask, mode='RGB')
                buffer = io.BytesIO()
                mask_image.save(buffer, format='PNG')
                mask_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            # Calculate only verifiable measurements from segmentation data
            lesion_present = bool(segmented_pixels > 0)  # Convert numpy bool to Python bool
            lesion_percentage = float(segmentation_percentage)  # Ensure Python float
            
            # Generate basic insights based only on segmentation results
            insights = []
            if lesion_present:
                insights.append("Lesion detected in ultrasound image")
                insights.append(f"Lesion covers {lesion_percentage:.2f}% of the image area")
            else:
                insights.append("No lesions detected in the ultrasound image")
            
            # Generate basic recommendations
            recommendations = []
            if lesion_present:
                recommendations.append("Consult with a radiologist for detailed analysis")
                recommendations.append("Consider additional imaging studies for confirmation")
            else:
                recommendations.append("Continue regular breast screening schedule")
            
            return {
                "success": True,
                "segmentation_mask": mask_base64,
                "statistics": {
                    "total_pixels": int(total_pixels),
                    "segmented_pixels": int(segmented_pixels),
                    "segmentation_percentage": float(segmentation_percentage)
                },
                "measurements": {
                    "lesion_percentage": lesion_percentage,
                    "lesion_present": lesion_present,
                    "total_pixel_count": int(total_pixels),
                    "segmented_pixel_count": int(segmented_pixels)
                },
                "insights": insights,
                "recommendations": recommendations,
                "message": "Breast ultrasound segmentation completed successfully"
            }
            
        except Exception as e:
            logger.error(f"Error in breast ultrasound segmentation: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to segment breast ultrasound image"
            }


# Singleton instance for reuse
breast_segmentation_service = BreastSegmentationService()
