from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import httpx

router = APIRouter()

@router.get("/proxy-glb")
async def proxy_glb(url: str):
    """Proxy GLB files from Ready Player Me to avoid CORS issues"""
    try:
        # Add morphTargets=Oculus Visemes to get viseme blend shapes
        if '?' in url:
            proxied_url = f"{url}&morphTargets=Oculus Visemes"
        else:
            proxied_url = f"{url}?morphTargets=Oculus Visemes"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(proxied_url, timeout=30.0)
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Failed to fetch GLB")
            
            return StreamingResponse(
                iter([response.content]),
                media_type="model/gltf-binary",
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Cache-Control": "public, max-age=31536000"
                }
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
