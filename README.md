# Stratum Android Examples (v0.2) – Chaquopy + Python 3.10

This repository contains Android example projects demonstrating how to use **Stratum v0.2** with **Python (via Chaquopy)**.

---

## 📦 Included Examples

* `example_camera`
* `example_camera_opencv`
* `example_counter`
* `example_webview`
* `example_xml_ui`

---

## ⚙️ Requirements

* Android Studio
* Python **3.10**
* Java **17**

> ⚠️ These examples are specifically built for **Stratum v0.2** and **Python 3.10**

---

## Python 3.10 + Chaquopy Setup

These projects use **Chaquopy** to run Python inside Android.

### 🔹 Step 1: Install Python 3.10

Install Python 3.10 and note the path:

```text id="x4r2hj"
C:/Python310/python.exe
```

---

### 🔹 Step 2: Configure in `build.gradle` (Module: app)

```gradle id="o9b3kl"
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

### 🔹 Why Python 3.10 is Required?

* The included `.whl` (Stratum library) is built for **Python 3.10**
* Using another Python version may cause build/runtime issues
* Chaquopy uses your local Python to build dependencies

---

## 📁 Project Notes

### ✅ Stratum `.whl`

* Location: `app/libs/`
* Already included in each example
* Built for **Stratum v0.2 usage**

---

## 🚀 Run the Examples

1. Open any example in Android Studio
2. Sync Gradle
3. Run on device/emulator

---

## 🧩 `stratum_jsons` (Reference)

Inside each example:

```id="p2k7mz"
stratum_jsons/
 ├── 02_inspect/
 │    └── targets.json
 ├── 05_5_abstract/
 │    └── targets.json   (optional – not required for all examples)
 └── 05_resolve/
      └── targets.json
```

### 🔹 What are these?

* These JSON files are used in each example’s **Stratum library build**
* They are part of **Stratum v0.2 pipeline stages**

---

## 📌 Summary

* Built for **Stratum v0.2**
* Python **3.10 required**
* `.whl` already included → ready to run
* `stratum_jsons` used for Stratum build pipeline

---
