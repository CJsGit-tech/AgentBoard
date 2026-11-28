# JPG image uploads

This rule applies to every AgentBuild workflow and implementation-evidence handoff, including still images inside published canvas packages.

- Reject PNG uploads before transmission and tell the user: "PNG uploads are blocked. Convert to JPG format before uploading." This includes PNG bytes renamed to another extension and embedded PNG data in canvas HTML/CSS/scripts. Convert captures separately before calling an upload helper.

- Convert every image file intended for upload to genuine JPEG (`.jpg`, `image/jpeg`) before transmission. A renamed PNG is not a conversion. Keep original captures locally and upload a separate JPG copy.
- Start around quality 85, preserve readable text and details, and inspect the converted image before upload. Avoid repeated lossy conversions. Preserve dimensions unless the destination limit requires a reduction; do not upscale. Flatten transparency onto the intended screen background and preserve orientation and correct colors.
- Check the actual encoded format, filename and destination size limit. Record the JPG filename, byte size and SHA-256 of the converted bytes. Verify the saved digest and rendered preview against that JPG, not the original capture. Where useful, retain the original-to-JPG mapping locally.
- Convert image assets before final canvas packaging, update their references, and inspect the resulting canvas. HTML, CSS, scripts and fonts are not image files and keep their native formats. Existing published versions and attachments are not retroactively replaced by this rule.
- AgentBoard's `attach_visual` accepts JPEG through `image_base64` (`png_base64` is a legacy alias) and checks that the extension matches the bytes. The bundled `attach_visual.py` helper converts the original to a `.jpg` copy (quality 85, transparency flattened onto white), keeps the original, prints the JPG path, size and SHA-256, then uploads it. Before sending, confirm the connected server's `attach_visual` schema lists `image_base64`; if it does not, the server predates JPEG support, so keep the JPG locally and report an incomplete handoff instead of uploading PNG.

The existing approval, privacy, impact-review and evidence-completion requirements still apply.
