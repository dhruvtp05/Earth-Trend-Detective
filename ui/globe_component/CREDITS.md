# Globe component credits

- `globe.gl.min.js`: [globe.gl](https://github.com/vasturiano/globe.gl) v2.46.2
  by Vasco Asturiano, MIT License. Bundles three.js (MIT License).
- `earth-blue-marble.jpg` (4096 × 2048): NASA Blue Marble imagery (NASA Earth
  Observatory), as distributed with
  [three-globe](https://github.com/vasturiano/three-globe).
- `earth-2k.jpg` (2048 × 1024): the same image resized for this project. It is
  loaded first so the globe appears quickly; the larger file replaces it on
  large screens unless the browser asks to save data.
- `archivo-black-latin.woff2`: [Archivo Black](https://github.com/Omnibus-Type/Archivo)
  by Omnibus-Type, SIL Open Font License 1.1. Latin subset as served by Google
  Fonts. Used for the title and the region names.

These files are stored here so the app does not load them from an outside
server at run time.
