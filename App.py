import streamlit as st
import yt_dlp
import subprocess
import os
from pathlib import Path
import re

# --- Custom CSS for Stylish Buttons ---
st.markdown("""
<style>
/* Style for the main action button ('Fetch Media') */
div.stButton > button:first-child {
    background: linear-gradient(90deg, #FF4B2B, #FF416C);
    color: white;
    font-size: 18px;
    font-weight: bold;
    padding: 12px 30px;
    border: none;
    border-radius: 50px; /* Makes it a pill shape */
    box-shadow: 0 4px 14px 0 rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease-in-out;
    width: 100%;
}

div.stButton > button:first-child:hover {
    transform: scale(1.03);
    box-shadow: 0 6px 20px 0 rgba(0, 0, 0, 0.2);
}

/* Style for the file download button */
div.stDownloadButton > button:first-child {
    background: linear-gradient(90deg, #FF4B2B, #FF416C);
    color: white;
    font-size: 18px;
    font-weight: bold;
    padding: 12px 30px;
    border: none;
    border-radius: 50px;
    box-shadow: 0 4px 14px 0 rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease-in-out;
    width: 100%;
}

div.stDownloadButton > button:first-child:hover {
    transform: scale(1.03);
    box-shadow: 0 6px 20px 0 rgba(0, 0, 0, 0.2);
}
</style>
""", unsafe_allow_html=True)

# --- Helper Function to Create Safe Filenames ---
def sanitize_filename(text):
    """
    Removes or replaces illegal filename characters from text.
    """
    return re.sub(r'[\\/*?:"<>|]', "", text)

# --- Twitter Video Downloader Class ---
class HighQualityTwitterDownloader:
    """
    Downloads Twitter media in MAXIMUM quality
    - Videos: yt-dlp (best quality)
    - Images: gallery-dl (original quality)
    """
    
    def __init__(self, output_folder='downloads_hq', verbose=False):
        self.output_folder = output_folder
        self.verbose = verbose
        os.makedirs(output_folder, exist_ok=True)
    
    def _print(self, message, force=False):
        """Print only if verbose mode is on or force is True"""
        if self.verbose or force:
            print(message)
    
    def download_video_max_quality(self, tweet_url):
        """Download video in highest quality"""
        ydl_opts = {
            'outtmpl': f'{self.output_folder}/%(id)s_%(height)sp.%(ext)s',
            'format': (
                'bestvideo[ext=mp4][vcodec^=avc1]+bestaudio[ext=m4a]/'
                'bestvideo[ext=mp4]+bestaudio[ext=m4a]/'
                'bestvideo+bestaudio/'
                'best'
            ),
            'merge_output_format': 'mp4',
            'postprocessor_args': ['-c:v', 'copy', '-c:a', 'copy'],
            'writethumbnail': False,
            'write_info_json': False,
            'quiet': True,
            'no_warnings': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                self._print("  Downloading video...")
                info = ydl.extract_info(tweet_url, download=True)
                
                filename = f"{self.output_folder}/{info['id']}_{info.get('height')}p.{info['ext']}"
                size_mb = os.path.getsize(filename) / (1024 * 1024) if os.path.exists(filename) else 0
                
                return {
                    'success': True,
                    'type': 'video',
                    'resolution': f"{info.get('width')}x{info.get('height')}",
                    'fps': info.get('fps'),
                    'size_mb': round(size_mb, 2),
                    'filename': filename
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def download_images_max_quality(self, tweet_url):
        """Download images in original quality"""
        try:
            cmd = [
                'gallery-dl',
                '--destination', self.output_folder,
                '--filename', '{category}_{tweet_id}_{num}.{extension}',
                '--quiet',
                tweet_url
            ]
            
            self._print("  Downloading images...")
            
            # Get files before download
            before = set(Path(self.output_folder).glob('*'))
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            # Get files after download
            after = set(Path(self.output_folder).glob('*'))
            new_files = after - before
            
            if result.returncode == 0 and new_files:
                total_size = sum(f.stat().st_size for f in new_files) / (1024 * 1024)
                
                return {
                    'success': True,
                    'type': 'images',
                    'count': len(new_files),
                    'size_mb': round(total_size, 2),
                    'files': [str(f) for f in new_files]
                }
            else:
                return {'success': False, 'error': result.stderr or 'No images found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def download(self, tweet_url):
        """Download media from tweet (auto-detects type)"""
        self._print(f"\nDownloading: {tweet_url}", force=not self.verbose)
        
        # Try video first
        video_result = self.download_video_max_quality(tweet_url)
        
        if video_result['success']:
            video_result['url'] = tweet_url
            return video_result
        
        # Try images
        image_result = self.download_images_max_quality(tweet_url)
        
        if image_result['success']:
            image_result['url'] = tweet_url
            return image_result
        else:
            return image_result

# --- Core Download Function ---
def download_twitter_media(video_url):
    """
    Downloads Twitter media using the HighQualityTwitterDownloader class.
    Returns a tuple: (result_dict, error_message).
    """
    try:
        downloader = HighQualityTwitterDownloader(output_folder='twitter_downloads')
        result = downloader.download(video_url)
        
        if result['success']:
            return result, None
        else:
            error_msg = result.get('error', 'Unknown error')
            user_friendly_error = f"❌ {error_msg}"
            return None, user_friendly_error
            
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        user_friendly_error = "❌ An unexpected error occurred. Please try again later."
        return None, user_friendly_error

# --- Streamlit User Interface ---
st.set_page_config(page_title="Twitter Media Downloader", layout="centered")

st.title("🐦 Free Twitter Media Downloader")
st.write("Paste a Twitter/X video or image URL below to download **high-quality** media without any watermark.")

url = st.text_input("Enter **Twitter/X** Media URL:", placeholder="https://x.com/username/status/123...", label_visibility="collapsed")

show_preview = st.toggle("Show media preview", value=True, help="If enabled, a preview of the media will be shown after loading.")

if st.button("⬇️ Fetch Media"):
    if url:
        with st.spinner("Fetching and downloading your media... Please wait."):
            result, error_msg = download_twitter_media(url)

            if error_msg:
                st.error(error_msg)
            elif result:
                # Handle Video
                if result.get('type') == 'video':
                    video_path = result.get('filename')
                    
                    if video_path and os.path.exists(video_path):
                        st.success(f"✅ Video loaded successfully! ({result.get('resolution')} • {result.get('size_mb')} MB)")

                        with open(video_path, "rb") as file:
                            video_bytes = file.read()
                        
                        if show_preview:
                            st.video(video_bytes)

                        spacer_col, button_col = st.columns([2, 1])

                        with button_col:
                            st.download_button(
                                label="Download Video",
                                data=video_bytes,
                                file_name=os.path.basename(video_path),
                                mime="video/mp4"
                            )

                        # Clean up
                        os.remove(video_path)
                
                # Handle Images
                elif result.get('type') == 'images':
                    image_files = result.get('files', [])
                    
                    if image_files:
                        st.success(f"✅ {result.get('count')} image(s) loaded successfully! ({result.get('size_mb')} MB)")
                        
                        if show_preview:
                            # Show all images in preview
                            cols = st.columns(min(len(image_files), 3))
                            for idx, img_path in enumerate(image_files):
                                with cols[idx % 3]:
                                    st.image(img_path, use_container_width=True)
                        
                        # Download buttons for each image
                        st.write("---")
                        for idx, img_path in enumerate(image_files):
                            if os.path.exists(img_path):
                                with open(img_path, "rb") as file:
                                    img_bytes = file.read()
                                
                                # Create columns for better layout
                                if len(image_files) > 1:
                                    col1, col2 = st.columns([3, 1])
                                    with col1:
                                        st.write(f"**Image {idx + 1}**")
                                    with col2:
                                        st.download_button(
                                            label=f"Download",
                                            data=img_bytes,
                                            file_name=os.path.basename(img_path),
                                            mime="image/jpeg",
                                            key=f"download_{idx}"
                                        )
                                else:
                                    st.download_button(
                                        label="Download Image",
                                        data=img_bytes,
                                        file_name=os.path.basename(img_path),
                                        mime="image/jpeg"
                                    )
                                
                                # Clean up
                                os.remove(img_path)
    else:
        st.warning("Please enter a Twitter/X URL.")
