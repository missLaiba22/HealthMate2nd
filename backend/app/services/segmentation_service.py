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


# Singleton instance for reuse
segmentation_service = SegmentationService()


