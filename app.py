from flask import Flask, render_template, request, send_file, flash, redirect, url_for # type: ignore
from PIL import Image # type: ignore
import os
import io

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Configuration
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp'}

# Check if the file extension is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to encode the message into the image
def encode_message(image_file, message):
    try:
        # Open the uploaded image
        image = Image.open(image_file)
        encoded_image = image.copy()

        # Convert message to binary and add a termination sequence
        binary_message = ''.join(format(ord(char), '08b') for char in message) + '00000000'

        # Get image dimensions
        width, height = encoded_image.size
        index = 0

        # Iterate through the pixels and encode the message
        for y in range(height):
            for x in range(width):
                pixel = list(encoded_image.getpixel((x, y)))  # Get the pixel as a list of RGB values

                for i in range(3):  # Only modify RGB channels
                    if index < len(binary_message):
                        pixel[i] = (pixel[i] & ~1) | int(binary_message[index])
                        index += 1

                encoded_image.putpixel((x, y), tuple(pixel))

                if index >= len(binary_message):
                    break
            if index >= len(binary_message):
                break

        # Save the encoded image to a BytesIO object
        output = io.BytesIO()
        encoded_image.save(output, format='PNG')
        output.seek(0)

        return output
    except Exception as e:
        print(f"Error encoding message: {e}")
        return None

# Function to decode the message from the image
def decode_message(image_file):
    try:
        # Open the uploaded image
        image = Image.open(image_file)
        binary_message = ''
        width, height = image.size

        # Iterate through the pixels to decode the message
        for y in range(height):
            for x in range(width):
                pixel = list(image.getpixel((x, y)))

                for i in range(3):  # Extract from RGB channels
                    binary_message += str(pixel[i] & 1)

        # Convert binary message to text
        message = ''
        for i in range(0, len(binary_message), 8):
            byte = binary_message[i:i+8]
            if byte == '00000000':  # Stop at termination sequence
                break
            message += chr(int(byte, 2))

        return message
    except Exception as e:
        print(f"Error decoding message: {e}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/encode', methods=['POST'])
def encode():
    image = request.files['image']
    message = request.form['message']

    if not allowed_file(image.filename):
        flash("Unsupported file format. Please upload a PNG, JPG, or BMP image.")
        return redirect(url_for('index'))

    if image.content_length > MAX_FILE_SIZE:
        flash("File size exceeds the 5MB limit. Please upload a smaller image.")
        return redirect(url_for('index'))

    encoded_image = encode_message(image, message)

    if encoded_image is None:
        flash("Failed to encode the message. Please try again.")
        return redirect(url_for('index'))

    return send_file(encoded_image, as_attachment=True, download_name="encoded_image.png")

@app.route('/decode', methods=['POST'])
def decode():
    image = request.files['image']

    if not allowed_file(image.filename):
        flash("Unsupported file format. Please upload a PNG, JPG, or BMP image.")
        return redirect(url_for('index'))

    if image.content_length > MAX_FILE_SIZE:
        flash("File size exceeds the 5MB limit. Please upload a smaller image.")
        return redirect(url_for('index'))

    hidden_message = decode_message(image)

    if hidden_message is None:
        flash("Failed to decode the message. Please try again.")
        return redirect(url_for('index'))

    return f"The hidden message is: {hidden_message}"

if __name__ == '__main__':
    app.run(debug=True)
