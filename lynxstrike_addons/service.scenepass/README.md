## <p align="center"><ins>ScenePass for KODI</ins></p>

<p align="center"><strong>Skip TV intros and recaps, Netflix-style.</strong></p>

<p align="center"><strong>ScenePass is a Kodi service add-on that reads <code>.sp.json</code> sidecar files sitting next to your video files and automatically detects intro and recap segments during playback — offering on-screen Skip Intro / Skip Recap buttons, or auto-skipping them entirely.
</strong></p>

---

### 🎬 <ins>Features</ins>

- Reads ScenePass `.sp.json` sidecars next to each video file — no extra scanning inside Kodi
- On-screen **Skip Intro** / **Skip Recap** pill buttons during playback (not a blocking dialog)
- Optional automatic skipping, independently for intros and recaps
- Confidence and minimum-segment-duration gates, so low-confidence detections are ignored

---

### 📦 <ins>Installation</ins>

Once you've added the `lynxstrike.repo` source in Kodi (see the [repository README](../../README.md) for those steps):

**System > Add-ons > Install from repository** → select **lynxstrike.repo** → **Services** → click **ScenePass** to install.

The service starts automatically and watches for `.sp.json` sidecars alongside the video currently playing.

---

### ⚙️ <ins>Settings</ins>

Configure via **Add-ons > My add-ons > Services > ScenePass > Configure**:

**Skip behaviour**
- Enable intro skip / Enable recap skip
- Automatically skip intros / Automatically skip recaps

**Quality gates**
- Minimum confidence (0–100%, default 75%)
- Minimum segment length in seconds (default 5s)
- Debug logging

---

### 🌐 <ins>Translations</ins>

English (en_GB) only at present.

---

### 🤖 <ins>AI-Generated Content Disclosure</ins>

This add-on's source code, and its icon/fanart artwork, were generated with the assistance of AI tools. Provided for transparency and regulatory compliance.

---

### 📄 <ins>License</ins>

MIT.

---

### 📬 <ins>Contact & Support</ins>

For bug reports, create a GitHub issue on this repository.
