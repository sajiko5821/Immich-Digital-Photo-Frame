## Immich Photo Processor for Slideshows

This Python script is designed to synchronize photos from a specific Immich album to a local directory, process them for a consistent slideshow aspect ratio (16:10), and then prepare them for use in external applications like a Home Assistant media player.

The script ensures upright (portrait) images are presented correctly in a widescreen display by adding a blurred, darkened background, while horizontal (landscape) images are cropped to the target ratio.

-----

### ✨ Features

  * **Immich Integration:** Fetches asset paths from a specified Immich album via API.
  * **Local Synchronization:** Copies image files from a local Immich backup directory into a processing catalog.
  * **Processing Check:** Uses a `processed.csv` file to track and skip images that have already been processed, allowing for incremental runs.
  * **Format Conversion:** Converts `.png` files to high-quality `.jpg` format for compatibility.
  * **Aspect Ratio Correction:**
      * **Landscape Images:** Center-crops horizontal images to fit the target 16:10 aspect ratio.
      * **Portrait Images:** Embeds vertical images onto a 16:10 canvas with a blurred and darkened version of the image used as the background "bars."
  * **EXIF Orientation Correction:** Automatically rotates images based on embedded EXIF data.
  * **Randomization:** Shuffles the final processed files and renames them numerically (e.g., `1.jpg`, `2.jpg`) for random slideshow order on each sync.
  * **Cleanup:** Clears the temporary working folder after a successful run.

-----

### ⚙️ Prerequisites

Before running the script, ensure you have the following installed:

1.  **Python 3**
2.  **Required Libraries:**
    ```bash
    pip install requests Pillow
    ```

-----

### 🚀 Setup and Configuration

You need to set up the following configuration variables within the `if __name__ == "__main__":` block of the script:

1.  **Immich API Details**

      * `buero_album_url`: The full Immich API endpoint for the album you want to sync (e.g., `https://<IMMICH_URL>/api/albums/<ALBUM_ID>`).
      * `buero_api_key`: Your Immich API key.

2.  **Local Directory Paths**

      * `source_directory`: The local path to the root of your Immich data/upload folder (where the images are stored locally).
      * `common_path`: The path to the parent directory where the script will create its working folders (`/catalog`, `/working`, `/done`).
      * `ha_path`: The final destination folder for the processed images (e.g., the folder used by your Home Assistant slideshow component).

3.  **Processing Parameters**

      * `target_width` / `target_height`: The desired aspect ratio (currently set to 16:10).
      * `blur_factor`: Controls the intensity of the blur applied to the background bars (higher value = more blur).
      * `background_brightness`: Controls the darkness of the background bars (e.g., `0.75` for $75\%$ brightness).

### 📂 Folder Structure

The script manages three main folders within the `common_path`:

| Folder | Purpose |
| :--- | :--- |
| **catalog** | Stores a copy of all images fetched from the Immich album. |
| **working** | Temporary folder used for format conversion and initial processing steps. Cleared after each run. |
| **done** | Stores the final processed images (16:10 aspect ratio). These files are renamed and then copied to the final Home Assistant path. |

-----

### 📝 Usage

After setting up the prerequisites and configuration variables, you can run the script from your terminal:

```bash
python3 transform.py
```

It is recommended to schedule this script to run periodically (e.g., daily using a cron job or systemd timer) to keep your slideshow content synchronized with the Immich album.
