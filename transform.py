import requests
import random
import string
import json
import csv
import os
from PIL import Image, ImageFilter, ImageEnhance, ExifTags

def fetch_album_data(url, api_key, source_directory, catalog_path):
    headers = {'Accept': 'application/json', 'x-api-key': api_key}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        try:
            data = json.loads(response.text)
            assets = data.get('assets', [])
            for asset in assets:
                original_path = asset.get('originalPath')
                if original_path:
                    source_path = source_directory + original_path.replace('/photos', '')
                    copy_album_to_local(source_path, source_directory, catalog_path)
        except json.JSONDecodeError as e:
            print("Error parsing JSON:", str(e))
    else:
        print(f"Failed to retrieve data. Status Code: {response.status_code}")

def copy_album_to_local(original_path, source_directory, catalog_path):    
    source_path = os.path.join(source_directory, original_path)
    os.makedirs(catalog_path, exist_ok=True)
    destination_path = os.path.join(catalog_path, os.path.basename(original_path))

    if not os.path.exists(destination_path):
        try:
            with open(source_path, 'rb') as source_file, open(destination_path, 'wb') as destination_file:
                chunk_size = 1024
                while True:
                    chunk = source_file.read(chunk_size)
                    if not chunk:
                        break
                    destination_file.write(chunk)
        except FileNotFoundError:
            print(f"File not found: {source_path}")
        except Exception as e:
            print(f"Error copying file: {str(e)}")
            
def load_processed_filenames(processed_csv):
    global processed_filenames
    try:
        with open(processed_csv, 'r', newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                filename = row['Filename']
                processed_filenames[filename] = True
    except FileNotFoundError:
        pass

def copy_files(source_directory, destination_directory, extensions):
    os.makedirs(destination_directory, exist_ok=True)

    for filename in os.listdir(source_directory):
        if filename.lower().endswith(extensions) and filename and not is_processed(filename):
            source_path = os.path.join(source_directory, filename)
            destination_path = os.path.join(destination_directory, filename)
            if not os.path.exists(destination_path):
                try:
                    with open(source_path, 'rb') as source_file, open(destination_path, 'wb') as destination_file:
                        destination_file.write(source_file.read())
                    print(f"File copied: {filename}")
                except FileNotFoundError:
                    print(f"File not found: {source_path}")
                except Exception as e:
                    print(f"Error copying file: {str(e)}")
            else:
                print(f"File already exists: {filename}")

def convert_png_to_jpg(input_path, quality=95):
    try:
        # Open the PNG image
        png_image = Image.open(input_path)

        # Convert and save as JPG
        jpg_output_path = os.path.splitext(input_path)[0] + '.jpg'
        png_image.convert('RGB').save(jpg_output_path, 'jpg', quality=quality)
        print(f"Converted {input_path} to {jpg_output_path}")

        # Optionally, you can remove the original PNG file here
        os.remove(input_path)
    except Exception as e:
        print(f"Error converting {input_path}: {e}")

def rename_jpeg_files_in_directory(directory):
    for filename in os.listdir(directory):
        if filename.lower().endswith(('.jpeg', '.jpg', '.JPG')):
            old_path = os.path.join(directory, filename)
            new_extension = ".jpg"
            new_name = os.path.splitext(filename)[0] + new_extension
            new_path = os.path.join(directory, new_name)

            while os.path.exists(new_path):
                new_name = os.path.splitext(new_name)[0] + "_1" + new_extension
                new_path = os.path.join(directory, new_name)

            os.rename(old_path, new_path)

def process_images_in_working_folder(working_path, done_path):
    # Ensure the output folder exists
    if not os.path.exists(done_path):
        os.makedirs(done_path)

    # Process each image in the input folder
    for filename in os.listdir(working_path):
        if filename.endswith(('.jpg', '.png', '.jpeg', '.JPG')) and filename and not is_processed(filename):
            image_path = os.path.join(working_path, filename)
            output_path = os.path.join(done_path, filename)

            print(f"Processing {filename}...")

            try:
                # Open the image
                image = Image.open(image_path)

                # Remove Exif orientation information
                exif = image._getexif()
                if exif is not None:
                    for orientation in ExifTags.TAGS.keys():
                        if ExifTags.TAGS[orientation] == 'Orientation':
                            break

                    if orientation in exif:
                        if exif[orientation] == 3:
                            image = image.rotate(180, expand=True)
                        elif exif[orientation] == 6:
                            image = image.rotate(270, expand=True)
                        elif exif[orientation] == 8:
                            image = image.rotate(90, expand=True)

                width, height = image.size
                
                # Check if the image is horizontal
                if width > height:
                    # Calculate the dimensions for cropping to target aspect ratio
                    target_ratio = target_width / target_height
                    current_ratio = width / height

                    if current_ratio > target_ratio:
                        # Crop the image horizontally to match the target aspect ratio
                        new_width = int(height * target_ratio)
                        left_margin = (width - new_width) // 2
                        right_margin = width - left_margin
                        image = image.crop((left_margin, 0, right_margin, height))

                # Check if the image is upright
                if width < height:
                    # Calculate the dimensions for the canvas
                    canvas_width = int(height * target_width / target_height)
                    canvas_height = height

                    # Calculate the dimensions for the zoomed background image
                    bg_width = canvas_width
                    bg_height = int(canvas_width * height / width)

                    # Resize the background image for zooming
                    background_image = image.resize((bg_width, bg_height))

                    # Apply blur to the background image
                    blurred_image = background_image.filter(ImageFilter.GaussianBlur(blur_factor))

                    # Darken the background image
                    enhancer = ImageEnhance.Brightness(blurred_image)
                    darkened_background = enhancer.enhance(background_brightness)

                    # Create a new canvas with the darkened background image
                    canvas = Image.new("RGB", (canvas_width, canvas_height))
                    canvas.paste(darkened_background, (0, (canvas_height - bg_height) // 2))

                    # Paste the original image in the center of the canvas
                    offset = ((canvas_width - width) // 2, 0)
                    canvas.paste(image, offset)

                    # Save the modified image
                    canvas.save(output_path)

                else:
                    # Image is already upright, no modifications needed
                    image.save(output_path)
                
                # Mark image as processed
                mark_as_processed(filename)

            except Exception as e:
                print(f"Error processing {filename}: {e}")
                continue

    print("Image processing complete.")

def is_processed(filename):
    global processed_filenames
    return filename in processed_filenames

def mark_as_processed(filename):
    global processed_filenames
    processed_filenames[filename] = True
    
def save_processed_filenames(csv_file):
    global processed_filenames
    try:
        with open(csv_file, 'w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=['Filename'])
            writer.writeheader()
            for filename in processed_filenames.keys():
                writer.writerow({'Filename': filename})
    except Exception as e:
        print(f"Error saving processed files: {e}")

def delete_files_in_folder(folder_path):
    try:
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
        print("Files in the working folder deleted successfully.")
    except Exception as e:
        print(f"Error deleting files in the working folder: {e}")

def shuffle_and_rename(done_path):
    # Get a list of all files in the folder with supported extensions
    files = [f for f in os.listdir(done_path) if f.endswith(('.jpg', '.png', '.jpeg', '.JPG'))]

    # Shuffle the files randomly
    random.shuffle(files)

    # Renaming with unique identifiers while avoiding overwriting
    for i, old_name in enumerate(files, start=1):
        base_name, extension = os.path.splitext(old_name)
        new_name = f'{i}_{generate_unique_identifier()}{extension}'
        while os.path.exists(os.path.join(done_path, new_name)):
            new_name = f'{i}_{generate_unique_identifier()}{extension}'
        os.rename(os.path.join(done_path, old_name), os.path.join(done_path, new_name))
    
    # Renaming to remove the unique identifiers
    for filename in os.listdir(done_path):
        if filename.endswith(('.jpg', '.png', '.jpeg', '.JPG')):
            old_path = os.path.join(done_path, filename)
            parts = filename.split('_')
            new_name = parts[0] + '.' + parts[-1].split('.')[-1]
            new_path = os.path.join(done_path, new_name)
            os.rename(old_path, new_path)

def generate_unique_identifier(length=5):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

if __name__ == "__main__":
    # Define Immich Album Endpoint
    buero_album_url = "https://<IMMICH_URL>/api/albums/<ALBUM_ID>"
    buero_api_key = '<API_KEY>'
    
    # Define paths as variables
    source_directory = r"<LOCAL_IMMICH_PATH>"
    common_path = r"<LOCAL_WORKING_DIRECTORY>"
    ha_path = r"<SLIDESHOW_FOLDER>"
    
    catalog_path = os.path.join(common_path, "catalog")
    working_path = os.path.join(common_path, "working")
    done_path = os.path.join(common_path, "done")
    processed_file_path = os.path.join(common_path, "processed.csv")
    
    # Global dictionary to store processed filenames
    processed_filenames = {}
    
    # Set the target aspect ratio (16:9)
    target_width = 16
    target_height = 10
    
    # Blur factor for the bars (higher values result in more blur)
    blur_factor = 5
    
    # Brightness factor for the background (1.0 is normal, values < 1 make it darker)
    background_brightness = 0.75

    # Get album paths
    fetch_album_data(buero_album_url, buero_api_key, source_directory, catalog_path)

    # Load already processed files
    load_processed_filenames(processed_file_path)

    # Copy PNG files to /working
    copy_files(catalog_path, working_path, ('.png',))
    
    # Convert all .png to .jpg
    for filename in os.listdir(working_path):
        if filename.lower().endswith('.png'):
            png_file_path = os.path.join(working_path, filename)
            convert_png_to_jpg(png_file_path)

    # Copy JPG files to /working
    copy_files(catalog_path, working_path, ('.jpg', '.jpeg', '.JPG'))

    # Rename .jpeg and .JPG files in the /working folder
    rename_jpeg_files_in_directory(working_path)

    # Process images in the /working directory and copy to /done
    process_images_in_working_folder(working_path, done_path)
    
    # Save the processed filenames to the CSV file
    save_processed_filenames(processed_file_path)

    # Delete files in the /working folder
    delete_files_in_folder(working_path)

    # Shuffle all files
    shuffle_and_rename(done_path)
    
    # Copy files to Home Assistant
    copy_files(done_path, ha_path, ('.jpg'))
