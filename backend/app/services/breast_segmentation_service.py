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
        return preds


# Singleton instance for reuse
breast_segmentation_service = BreastSegmentationService()
