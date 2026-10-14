const { getDefaultConfig } = require('expo/metro-config');

const config = getDefaultConfig(__dirname);

// Metro activo "package exports" por defecto a partir del SDK 57. El SDK de Firebase
// (firebase/auth) todavia no declara bien la condicion de React Native en su mapa de
// "exports", asi que con esto activado Metro resuelve un build distinto para
// "firebase/app" y "firebase/auth" y tira "Component auth has not been registered yet".
// Desactivarlo vuelve a la resolucion clasica por "main"/"browser", que es la que
// Firebase soporta correctamente en este momento.
config.resolver.unstable_enablePackageExports = false;

module.exports = config;
