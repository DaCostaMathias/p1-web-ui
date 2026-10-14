import createPspCrypto from './psp-encryption.js';

const bundledGameKey = Uint8Array.from({ length: 16 }, (_, index) => index);
let modulePromise;

async function getModule() {
  if (!modulePromise) {
    modulePromise = createPspCrypto({ locateFile: () => `${import.meta.env.BASE_URL}psp-encryption.wasm` }).then(module => {
      module._kirk_init();
      return module;
    });
  }
  return modulePromise;
}

function copyToWasm(module, bytes) {
  const ptr = module._malloc(bytes.length);
  for (let index = 0; index < bytes.length; index += 1) module.setValue(ptr + index, bytes[index], 'i8');
  return ptr;
}

function copyFromWasm(module, ptr, length) {
  return Uint8Array.from({ length }, (_, index) => module.getValue(ptr + index, 'i8') & 0xff);
}

export async function decryptPspSave(encryptedBytes) {
  if (encryptedBytes.length !== 19352) {
    throw new Error('Expected a 19,352-byte encrypted Persona 1 PSP save.');
  }
  const module = await getModule();
  const dataPtr = copyToWasm(module, encryptedBytes);
  const keyPtr = copyToWasm(module, bundledGameKey);
  const lengthPtr = module._malloc(4);
  module.setValue(lengthPtr, encryptedBytes.length, 'i32');

  try {
    const result = module.ccall('decrypt_save_buffer', 'number', ['number', 'number', 'number'], [dataPtr, lengthPtr, keyPtr]);
    if (result !== 0) throw new Error(`PSP decryption failed (code ${result}).`);
    const length = module.getValue(lengthPtr, 'i32');
    const decrypted = copyFromWasm(module, dataPtr, length);
    if (decrypted.length !== 19336 || new DataView(decrypted.buffer).getUint32(19332, true) !== 0x12345678) {
      throw new Error('The save did not decrypt to a valid Persona 1 PSP save.');
    }
    return decrypted;
  } finally {
    module._free(lengthPtr);
    module._free(keyPtr);
    module._free(dataPtr);
  }
}

export async function encryptPspSave(plainBytes, saveName = 'PERSONA.SAV', saveDirectory = 'ULUS104320000', templateDirectory = 'ULUS104320000', templateName = 'PSP-INPUT.SFO') {
  if (plainBytes.length !== 19336 || new DataView(plainBytes.buffer, plainBytes.byteOffset, plainBytes.byteLength).getUint32(19332, true) !== 0x12345678) {
    throw new Error('Expected a valid 19,336-byte unencrypted Persona 1 PSP save.');
  }
  if (!/^[A-Z0-9]{13}$/.test(saveDirectory)) throw new Error('The PSP save directory must be exactly 13 letters or numbers.');
  const module = await getModule();
  const sfoResponse = await fetch(`${import.meta.env.BASE_URL}${templateName}`);
  if (!sfoResponse.ok) throw new Error('Could not load the bundled PSP PARAM.SFO template.');
  const sfoBytes = new Uint8Array(await sfoResponse.arrayBuffer());
  const oldDirectory = new TextEncoder().encode(templateDirectory);
  const newDirectory = new TextEncoder().encode(saveDirectory);
  const directoryOffset = sfoBytes.findIndex((_, index) => oldDirectory.every((byte, position) => sfoBytes[index + position] === byte));
  if (directoryOffset < 0) throw new Error('Could not find the save directory field in PARAM.SFO.');
  sfoBytes.set(newDirectory, directoryOffset);
  const dataPtr = copyToWasm(module, plainBytes);
  const outputPtrPtr = module._malloc(4);
  const lengthPtr = module._malloc(4);
  const sfoPtr = copyToWasm(module, sfoBytes);
  const keyPtr = copyToWasm(module, bundledGameKey);
  module.setValue(outputPtrPtr, 0, 'i32');
  module.setValue(lengthPtr, plainBytes.length, 'i32');

  try {
    const result = module.ccall(
      'encrypt_save_buffer', 'number',
      ['number', 'number', 'number', 'number', 'number', 'string', 'number'],
      [dataPtr, outputPtrPtr, lengthPtr, sfoPtr, sfoBytes.length, saveName, keyPtr],
    );
    if (result !== 0) throw new Error(`PSP encryption failed (code ${result}).`);
    const encryptedPtr = module.getValue(outputPtrPtr, 'i32');
    const length = module.getValue(lengthPtr, 'i32');
    const encrypted = copyFromWasm(module, encryptedPtr, length);
    const updatedSfo = copyFromWasm(module, sfoPtr, sfoBytes.length);
    if (encrypted.length !== 19352) throw new Error(`Unexpected encrypted save size: ${encrypted.length} bytes.`);
    return { encrypted, paramSfo: updatedSfo };
  } finally {
    const encryptedPtr = module.getValue(outputPtrPtr, 'i32');
    if (encryptedPtr) module._free(encryptedPtr);
    module._free(dataPtr);
    module._free(outputPtrPtr);
    module._free(lengthPtr);
    module._free(sfoPtr);
    module._free(keyPtr);
  }
}
