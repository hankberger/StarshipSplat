# StarshipSplat

A Gaussian splat scene and flythrough built from a drone orbit video (`rocket1.mkv`) with the World Labs Atlas API.

- `rocket/frames/`, `rocket/scene/` - extracted frames and posed scene data
- `rocket/views*/`, `rocket/flyframes/`, `rocket/*.mp4` - generated views and flythrough videos
- `rocket/splats_*/` - Gaussian splats (`.spz`)
- `rocket/tools/`, `rocket/req/` - helper scripts and API request JSON

To view the splats, run `rocket/open_viewer.bat`.
