
---

# 🚀 Stratum Android Examples (v0.2) – Chaquopy + Python 3.10

<p align="center">
  <b>Android + Python integration using Stratum & Chaquopy</b><br/>
  Clean examples • Ready to run • Beginner friendly
</p>

---

## 📦 Included Examples

<div align="center">

| Example                 | Preview                                                                                                  |
| ----------------------- | -------------------------------------------------------------------------------------------------------- |
| `example_counter`       | <img src="https://github.com/user-attachments/assets/c4c6a004-f64c-4533-ae52-208716a5ed72" width="220"/> |
| `example_xml_ui`        | <img src="https://github.com/user-attachments/assets/7b7ee3f8-863f-4b39-8b48-9d5ee14cdc64" width="220"/> |
| `example_camera_opencv` | <sub>Canny Edge Detection</sub><br/><br/><img src="https://github.com/user-attachments/assets/27eec2fa-4aa9-4327-a9b3-964bcc263f0e" width="220"/> |

</div>

---

## ⚙️ Requirements

<div align="center">

| Tool           | Version  |
| -------------- | -------- |
| Android Studio | Latest   |
| Python         | **3.10** |
| Java           | **17**   |

</div>

> ⚠️ These examples are strictly built for **Stratum v0.2 + Python 3.10**

---

##  Python 3.10 + Chaquopy Setup

### 🔹 Step 1: Install Python 3.10

Install Python and note the path:

```text
C:/Python310/python.exe
```

---

### 🔹 Step 2: Configure `build.gradle` (Module: app)

```gradle
chaquopy {
    defaultConfig {
        version = "3.10"

        // Path to your local Python 3.10 installation
        buildPython("C:/Python310/python.exe")

        pip {
            // Use local .whl from libs folder
            options("--find-links", "${project.projectDir}/libs")

            // Install Stratum from local wheel
            install("stratum==0.1.0")
        }
    }
}
```

---

## ❓ Why Python 3.10?

* The included `.whl` is built specifically for **Python 3.10**
* Other versions may cause build or runtime issues
* Chaquopy depends on your local Python version

---

## 📁 Project Notes

### ✅ Stratum `.whl`

* 📍 Location: `app/libs/`
* Already included in all examples
* Built for **Stratum v0.2**

---

## ▶️ Run the Examples

```bash
1. Open project in Android Studio
2. Sync Gradle
3. Run on emulator/device
```

---

## 🧩 `stratum_jsons` Structure

```
stratum_jsons/
 ├── 02_inspect/
 │    └── targets.json
 ├── 05_5_abstract/
 │    └── targets.json   (optional)
 └── 05_resolve/
      └── targets.json
```

### 🔹 What is this?

* Defines **Stratum pipeline stages**
* Used internally by the Stratum build system
* Included for reference in each example

---

## 📌 Summary

* ✅ Built for **Stratum v0.2**
*  Requires **Python 3.10**
* 📦 `.whl` included → no extra setup
* ⚙️ Ready-to-run Android examples
* 🧩 Includes Stratum pipeline configs

---

## 💡 Tips

* Keep Python path correct in `build.gradle`
* Don’t upgrade Python unless `.whl` supports it
* If build fails → recheck Chaquopy config

---

<p align="center">
  💡 Are you using Stratum? Let us know what you think!<br/>
  Your feedback helps shape future updates and examples.
</p>

---
