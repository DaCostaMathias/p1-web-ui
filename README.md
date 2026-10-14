# Persona Save Studio

A browser-only React proof of concept inspired by the attached Persona 1 PSP Save Editor and Converter. The interface and edit flow are built in React; reference dictionaries from the archive live in `src/data` as static JSON. Save contents stay in memory; display naming preferences are stored in browser local storage.

## Run locally

Install dependencies with `npm install`, then start the Vite development server with `npm run dev`.

## Desktop build (Tauri)

The same code base also ships as a native desktop application via [Tauri 2](https://tauri.app/). The desktop target reuses the Vite build output in `dist/` and wraps it in a small Rust-powered WebView container.

### Prerequisites (one time per machine)

- Install Rust from <https://rustup.rs/> (adds `cargo` and the stable toolchain).
- On Windows, Tauri uses the system WebView2 runtime (shipped with recent Windows 10/11). On Linux, install the `webkit2gtk` development packages. On macOS, no extra setup is required.

### Workflows

| Task | Command | Opens in |
|---|---|---|
| UI / state / logic iteration | `npm run dev` | Browser at <http://localhost:5173> |
| Test native window + desktop integration | `npm run tauri:dev` | Native desktop window (also drives Vite with HMR) |
| Produce release installer | `npm run tauri:build` | Emits `.msi` / `.dmg` / `.AppImage` under `src-tauri/target/release/bundle/` |
| Browser-only release | `npm run build` | Produces `dist/` for static hosting |

`npm run dev` is unchanged by the desktop setup; it remains the fastest edit-and-reload loop. The Tauri configuration lives in `src-tauri/tauri.conf.json`; the Rust entry point is `src-tauri/src/lib.rs`. Rust build artifacts under `src-tauri/target/` and `src-tauri/gen/` are gitignored.

Save data continues to stay in memory on the desktop build; no server, filesystem watcher, or network call is added by Tauri.

## Current behavior

- Loads raw 14,336-byte PC saves (`.S00`–`.S06`, `.C00`–`.C06`) and Persona 1 PSP saves in the browser.
- Decrypts 19,352-byte PSP saves on import and edits their 19,336-byte plaintext save data.
- Re-encrypts edited PSP saves in mode 5. The default ZIP includes `PERSONA.SAV` and `PARAM.SFO` for direct use plus a plaintext `PERSONA.SAV` for Apollo Import Decrypted; plaintext-only export is also available. PC saves can be converted into the expanded PSP layout. Encrypted PSP export supports EU (`NPEH000690000`) and US (`ULUS104320000`) regions; choose the region beside Export save. The generated folder ID can also be edited in the Converter tab.
- Reads and edits party nicknames and protagonist first/last names, HP/SP, level, base and added stats, weapon values, character/persona experience and level, status, character modifier, seven equipment slots, save tag, money, coins, PSP/PS1 play time, PSP difficulty, 2D/3D overworld and 2D map modes, plus manual location/warp/floor/position/direction fields, and item identities and quantities. New items can use any available inventory slot. PC raw saves do not contain dedicated play-time or difficulty fields, and PS1 payloads do not store difficulty; those controls are enabled only for PSP output. Play time remains editable when converting to PSP or PS1.
- Edits persona identity, SP cost, level, stats, rank, owner, OMP/DMP, fourteen moves, equipped persona slots, and the 16-entry compendium; also edits twelve spell-card entries and selected story flags, and a Tools screen with bounded hex inspection and character/persona/move/item/spell-card ID lookups.
- Converts between PC, PSP, and PS1 save layouts, including character and persona records, names, US currency units, play time, location IDs, and form data. Region changes between supported PS1 US, Japanese, and Japanese suspend layouts are available. Exports PC saves to a selected slot with recalculated XOR checksums; PS1 output supports MCS memory-card saves and raw single-save files.
- Provides independent PSP, Revelations, and Japanese display naming tables for characters, personas, moves, items, equipment, demons, and locations.
- Includes demo values for exploring the UI; demo values cannot be exported as a save.
- Detects PC, US/Japanese PS1 MCS and raw single-save files, Persona saves inside supported PS1 memory-card images, encrypted/unencrypted PSP, and Japanese PSP saves. Memory-card images can be opened, an extracted Persona save selected, edited, and exported as a single `.mcs` save or PC raw save. PS1 raw saves can be edited and converted through the shared layout; PS1 exports are available as MCS or raw files for US, Japanese, and Japanese suspend variants.

## POC limits

The PSP crypto engine is compiled from the GPL-3.0 [psp-encryption-webassembly project](public/third-party/psp-encryption-webassembly/README.md); its corresponding source and license are included in `public/third-party/psp-encryption-webassembly`. The browser uses the `00 01 … 0F` game key bundled with the supplied Python editor. Japanese PSP import and encrypted export remain unsupported. Japanese first/last name decoding from PS1 saves follows the limited symbol table in the reference editor; the Converter tab lets you replace those names before applying the conversion. Memory-card extraction recognizes the US and Japanese Persona signatures from the reference tool; other game entries remain untouched in the source image, which is read-only. PS1 MCS export uses bundled format templates and does not rebuild or overwrite the source memory-card image. Location editing supports 2D overworld, 3D suspend, and 2D Mikage-cho map modes; manual location, warp, floor, X/Y position, and direction hex values can also be edited. Some story flag values overlap in the original format, so related outcomes should be reviewed together. US PSP export uses the bundled US SFO template and EU PSP export uses the EU template. Set the save directory to match your game folder. Back up imported saves before replacing them.

Field offsets and encoding were adapted from the Python editor in the provided archive. Bundled JSON tables provide local names for items, locations, status, characters, and other reference data.
