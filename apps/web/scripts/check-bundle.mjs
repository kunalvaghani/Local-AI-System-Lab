import { gzipSync } from "node:zlib";
import { readdirSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { extname, join } from "node:path";

const assetDirectory = fileURLToPath(new URL("../dist/assets/", import.meta.url));
const files = readdirSync(assetDirectory);
const javascriptFiles = files.filter((file) => extname(file) === ".js");
const maximumCompressedBytes = 250 * 1024;
const compressedBytes = javascriptFiles.reduce((total, file) => {
  const source = readFileSync(join(assetDirectory, file));
  return total + gzipSync(source).byteLength;
}, 0);

if (compressedBytes > maximumCompressedBytes) {
  throw new Error(`Initial JavaScript is ${compressedBytes} bytes gzip; budget is ${maximumCompressedBytes}`);
}

console.log(JSON.stringify({
  status: "PASS",
  javascriptFiles: javascriptFiles.length,
  compressedBytes,
  maximumCompressedBytes,
}));
