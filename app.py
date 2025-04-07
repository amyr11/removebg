import streamlit as st
from rembg import remove
from PIL import Image
import io
from streamlit_cropper import st_cropper  # Import the cropper component

# --- Streamlit App Setup ---
st.set_page_config(layout="wide", page_title="Background Remover & Cropper")

st.title("🖼️ Image Background Remover & Cropper")
st.markdown(
    """
Upload an image, remove background, set background color (using presets or picker),
and manually crop with a fixed aspect ratio. Crop selection persists when color changes.
"""
)

# --- Initialize Session State for Color ---
if "selected_color" not in st.session_state:
    st.session_state.selected_color = "#FFFFFF"  # Default to white

# --- Sidebar for Controls ---
st.sidebar.header("⚙️ Controls")

# 1. File Uploader
uploaded_file = st.sidebar.file_uploader(
    "1. Upload Your Image", type=["png", "jpg", "jpeg", "webp"]
)

# 2. Background Color Selection
st.sidebar.subheader("2. Background Color")
cols_sidebar = st.sidebar.columns(3)
if cols_sidebar[0].button("🟥 Red"):
    st.session_state.selected_color = "#FF0000"
if cols_sidebar[1].button("🟦 Blue"):
    st.session_state.selected_color = "#0000FF"
if cols_sidebar[2].button("⬜ White"):
    st.session_state.selected_color = "#FFFFFF"


def update_color_from_picker():
    st.session_state.selected_color = st.session_state.color_picker_value


bg_color = st.sidebar.color_picker(
    "Pick Custom Color",
    st.session_state.selected_color,
    key="color_picker_value",
    on_change=update_color_from_picker,
)

# 3. Crop Options
st.sidebar.subheader("3. Crop Settings")
crop_aspect_ratio_option = st.sidebar.selectbox(
    "Select Crop Aspect Ratio", ("No Crop", "1:1 (Square)", "35:45 (Passport)")
)

aspect_ratio = None
if crop_aspect_ratio_option == "1:1 (Square)":
    aspect_ratio = (1, 1)
elif crop_aspect_ratio_option == "35:45 (Passport)":
    aspect_ratio = (35, 45)

# --- Main Area ---
if uploaded_file is not None:
    try:
        # --- Processing Steps (outside columns first) ---
        input_bytes = uploaded_file.getvalue()
        # Use a unique key based on file content for caching the opened image if desired
        # For simplicity here, we just reopen it on rerun
        input_image = Image.open(io.BytesIO(input_bytes))

        # Step 1: Remove Background (Consider caching this step for performance)
        # @st.cache_data # Example caching decorator (might need adjustments)
        # def cached_remove_bg(img_bytes):
        #    img = Image.open(io.BytesIO(img_bytes))
        #    return remove(img)
        # output_image_nobg = cached_remove_bg(input_bytes)
        with st.spinner("Removing background..."):
            output_image_nobg = remove(input_image)

        # Step 2: Add Solid Background Color
        bg_color_hex = st.session_state.selected_color.lstrip("#")
        bg_color_rgb = tuple(int(bg_color_hex[i : i + 2], 16) for i in (0, 2, 4))
        background = Image.new("RGB", output_image_nobg.size, bg_color_rgb)
        try:
            background.paste(output_image_nobg, (0, 0), output_image_nobg)
        except ValueError as e:
            st.warning(
                f"Pasting with alpha mask failed ({e}), attempting direct paste."
            )
            background.paste(output_image_nobg, (0, 0))

        img_ready_for_crop = background  # Image with background color applied

        # --- Setup Columns for Display ---
        col1, col2 = st.columns(2)
        final_image = None  # Initialize final_image variable

        # --- Column 1: Interactive Cropper or Preview ---
        with col1:
            if crop_aspect_ratio_option != "No Crop":
                st.header("Crop Area (Adjust Box)")
                st.info("Adjust the blue box. The result appears on the right.")
                # Use st_cropper for manual cropping
                # --- KEY CHANGE HERE: Removed color from the key ---
                cropped_img = st_cropper(
                    img_ready_for_crop,
                    realtime_update=True,
                    box_color="blue",
                    aspect_ratio=aspect_ratio,
                    # Key now only depends on filename and crop setting
                    key=f"cropper_{uploaded_file.name}_{crop_aspect_ratio_option}",
                )
                final_image = cropped_img  # The result from the cropper

            else:
                st.header("Image Preview (No Crop)")
                st.info("Cropping is disabled. Result is shown on the right.")
                st.image(img_ready_for_crop, use_column_width=True)
                final_image = img_ready_for_crop  # No cropping needed

        # --- Column 2: Final Result Display ---
        with col2:
            st.header("Final Result")
            if final_image:
                st.image(final_image, caption="Processed Output", use_column_width=True)

                # --- Download Button (placed logically after final image is determined) ---
                buf = io.BytesIO()
                final_image_format = "PNG"
                if final_image.mode == "RGBA":
                    final_image.save(buf, format="PNG")
                else:
                    # Ensure it's RGB before saving if needed, PNG handles RGB fine.
                    if final_image.mode != "RGB":
                        final_image = final_image.convert("RGB")
                    final_image.save(buf, format="PNG")

                byte_im = buf.getvalue()

                try:
                    original_filename = uploaded_file.name.rsplit(".", 1)[0]
                except:
                    original_filename = "image"
                download_filename = f"{original_filename}_processed.png"

                # Place download button in sidebar for consistency
                st.sidebar.download_button(
                    label="4. Download Final Image",
                    data=byte_im,
                    file_name=download_filename,
                    mime="image/png",
                )
            else:
                st.warning("Waiting for image processing or cropping...")

    except Exception as e:
        st.error(f"❌ An error occurred during processing:")
        st.error(e)
        st.exception(e)  # Shows the full traceback for debugging
        st.error(
            "Please ensure the uploaded file is a valid image. Some images might fail background removal or processing."
        )

else:
    st.info("☝️ Upload an image using the sidebar controls to get started.")
