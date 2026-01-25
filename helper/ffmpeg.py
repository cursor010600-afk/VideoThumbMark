import os, time, asyncio, subprocess, json
from helper.utils import metadata_text

async def change_metadata(input_file, output_file, metadata):
    author, title, video_title, audio_title, subtitle_title = await metadata_text(metadata)
    
    # Get the video metadata
    output = subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-print_format', 'json', input_file])
    data = json.loads(output)
    streams = data['streams']

    # Create the FFmpeg command to change metadata
    cmd = [
        'ffmpeg',
        '-i', input_file,
        '-map', '0',  # Map all streams
        '-c:v', 'copy',  # Copy video stream
        '-c:a', 'copy',  # Copy audio stream
        '-c:s', 'copy',  # Copy subtitles stream
        '-metadata', f'title={title}',
        '-metadata', f'author={author}',
    ]

    # Add title to video stream
    for stream in streams:
        if stream['codec_type'] == 'video' and video_title:
            cmd.extend([f'-metadata:s:{stream["index"]}', f'title={video_title}'])
        elif stream['codec_type'] == 'audio' and audio_title:
            cmd.extend([f'-metadata:s:{stream["index"]}', f'title={audio_title}'])
        elif stream['codec_type'] == 'subtitle' and subtitle_title:
            cmd.extend([f'-metadata:s:{stream["index"]}', f'title={subtitle_title}'])

    cmd.extend(['-metadata', f'comment=Added by @Digital_Rename_Bot'])
    cmd.extend(['-f', 'matroska']) # support all format 
    cmd.append(output_file)
    print(cmd)
    
    # Execute the command
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print("FFmpeg Error:", e.stderr)
        return False

def detect_hardware_encoder():
    """
    Detect available hardware encoders for faster encoding
    Actually tests if the encoder works, not just if it's listed
    Returns: (encoder_name, preset_equivalent) or (None, None) if no GPU available
    """
    try:
        # Check for NVIDIA NVENC (most common)
        result = subprocess.run(
            ['ffmpeg', '-hide_banner', '-encoders'],
            capture_output=True, text=True, timeout=5
        )
        encoders = result.stdout
        
        # Priority order: NVIDIA > Intel > AMD (based on quality/speed)
        # Test each encoder to verify it actually works
        
        if 'h264_nvenc' in encoders:
            # Test NVIDIA NVENC by trying to encode a dummy frame
            print("[WATERMARK] Testing h264_nvenc availability...")
            test_result = subprocess.run(
                ['ffmpeg', '-hide_banner', '-f', 'lavfi', '-i', 'color=black:s=64x64:d=0.1',
                 '-c:v', 'h264_nvenc', '-f', 'null', '-'],
                capture_output=True, text=True, timeout=3
            )
            if test_result.returncode == 0:
                print("[WATERMARK] ✓ h264_nvenc is available and working")
                return ('h264_nvenc', 'p1')  # p1 = fastest preset for nvenc
            else:
                print(f"[WATERMARK] ✗ h264_nvenc listed but not working: {test_result.stderr[:200]}")
        
        if 'h264_qsv' in encoders:
            # Test Intel Quick Sync
            print("[WATERMARK] Testing h264_qsv availability...")
            test_result = subprocess.run(
                ['ffmpeg', '-hide_banner', '-f', 'lavfi', '-i', 'color=black:s=64x64:d=0.1',
                 '-c:v', 'h264_qsv', '-f', 'null', '-'],
                capture_output=True, text=True, timeout=3
            )
            if test_result.returncode == 0:
                print("[WATERMARK] ✓ h264_qsv is available and working")
                return ('h264_qsv', 'veryfast')  # veryfast for qsv
            else:
                print(f"[WATERMARK] ✗ h264_qsv listed but not working: {test_result.stderr[:200]}")
        
        if 'h264_amf' in encoders:
            # Test AMD AMF
            print("[WATERMARK] Testing h264_amf availability...")
            test_result = subprocess.run(
                ['ffmpeg', '-hide_banner', '-f', 'lavfi', '-i', 'color=black:s=64x64:d=0.1',
                 '-c:v', 'h264_amf', '-f', 'null', '-'],
                capture_output=True, text=True, timeout=3
            )
            if test_result.returncode == 0:
                print("[WATERMARK] ✓ h264_amf is available and working")
                return ('h264_amf', 'speed')  # speed preset for amf
            else:
                print(f"[WATERMARK] ✗ h264_amf listed but not working: {test_result.stderr[:200]}")
        
        print("[WATERMARK] No working hardware encoder found, will use CPU encoding")
        return (None, None)  # No hardware encoder available
    except Exception as e:
        print(f"[WATERMARK] Hardware encoder detection failed: {e}")
        return (None, None)


async def add_watermark(input_file, output_file, watermark_text="@Coursesbuying", position="bottom-right", status_message=None):
    """
    Add watermark text to video using FFmpeg
    position options: top-left, top-right, bottom-left, bottom-right, center, scroll-lr-center
    status_message: optional message object to update with progress
    """
    try:
        # Update status at start
        if status_message:
            try:
                await status_message.edit("`🎨 Adding watermark... please wait`")
            except:
                pass
        
        print(f"[WATERMARK] Starting watermark process for: {input_file}")
        print(f"[WATERMARK] Output file: {output_file}")
        print(f"[WATERMARK] Watermark text: {watermark_text}")
        print(f"[WATERMARK] Position: {position}")
        
        # Get video dimensions for positioning
        probe_cmd = [
            'ffprobe', '-v', 'error', '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height', '-of', 'json', input_file
        ]
        probe_output = subprocess.check_output(probe_cmd)
        probe_data = json.loads(probe_output)
        
        width = probe_data['streams'][0]['width']
        height = probe_data['streams'][0]['height']
        print(f"[WATERMARK] Video dimensions: {width}x{height}")

        # Calculate consistent font size based on video height (3.5% of height for good visibility)
        # This ensures same relative size across all videos
        fontsize = max(20, int(height * 0.035))  # Minimum 20px, scales with video height
        # Clamp to reasonable range (20-60px) for visibility
        fontsize = min(60, max(20, fontsize))
        print(f"[WATERMARK] Calculated font size: {fontsize}")

        # Get duration (for scrolling watermark and progress tracking)
        duration_seconds = 0.0
        try:
            dur_out = subprocess.check_output([
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                input_file
            ])
            duration_seconds = float(dur_out.decode("utf-8", errors="ignore").strip() or 0.0)
            print(f"[WATERMARK] Video duration: {duration_seconds}s")
        except Exception as e:
            print(f"[WATERMARK] Could not get duration: {e}")
            duration_seconds = 0.0
        
        # Calculate watermark position
        if position == "scroll-lr-center":
            # Scroll Left -> Right across the center of the video over the whole duration
            # x from 0 to (W-text_w)
            # y centered
            d = duration_seconds if duration_seconds > 0 else 1.0
            x = f"(W-text_w)*t/{d}"
            y = f"(H-text_h)/2"
        elif position == "top-left":
            x = f"10"  # 10 pixels from left
            y = f"10"  # 10 pixels from top
        elif position == "top-right":
            x = f"W-w-10"  # 10 pixels from right
            y = f"10"  # 10 pixels from top
        elif position == "bottom-left":
            x = f"10"  # 10 pixels from left
            y = f"H-h-10"  # 10 pixels from bottom
        elif position == "bottom-right":
            x = f"W-w-10"  # 10 pixels from right
            y = f"H-h-10"  # 10 pixels from bottom
        else:  # center
            x = f"(W-w)/2"
            y = f"(H-h)/2"
        
        print(f"[WATERMARK] Position formula - x: {x}, y: {y}")
        
        # Font file detection with fallback options
        # Priority: Environment variable > DejaVu > Liberation > Fallback to system default
        fontfile_candidates = [
            os.environ.get("WATERMARK_FONTFILE", ""),
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        ]
        
        fontfile = None
        for candidate in fontfile_candidates:
            if candidate and os.path.exists(candidate):
                fontfile = candidate
                print(f"[WATERMARK] ✓ Found font file: {fontfile}")
                break
            elif candidate:
                print(f"[WATERMARK] ✗ Font not found: {candidate}")
        
        if not fontfile:
            print("[WATERMARK] WARNING: No font file found, FFmpeg will use system default")
            print("[WATERMARK] This may cause the watermark to fail on some systems")
            # Use empty string to let FFmpeg try system default
            fontfile = ""
        
        # FFmpeg filter args need special escaping:
        # - use forward slashes
        # - escape ':' as '\:'
        if fontfile:
            fontfile_ffmpeg = fontfile.replace("\\", "/").replace(":", "\\:")
        else:
            fontfile_ffmpeg = ""

        # Basic escaping for drawtext
        escaped_text = watermark_text.replace("\\", "\\\\").replace("'", "\\'").replace(":", "\\:")

        # Box border width scales with font size for better visibility
        box_border = max(3, int(fontsize * 0.15))

        # Build drawtext filter - only include fontfile if we have one
        if fontfile_ffmpeg:
            drawtext = (
                f"drawtext="
                f"fontfile='{fontfile_ffmpeg}':"
                f"text='{escaped_text}':"
                f"fontcolor=white@0.9:fontsize={fontsize}:"
                f"x={x}:y={y}:"
                f"box=1:boxcolor=black@0.5:boxborderw={box_border}"
            )
        else:
            # No fontfile - let FFmpeg use system default
            drawtext = (
                f"drawtext="
                f"text='{escaped_text}':"
                f"fontcolor=white@0.9:fontsize={fontsize}:"
                f"x={x}:y={y}:"
                f"box=1:boxcolor=black@0.5:boxborderw={box_border}"
            )
        
        print(f"[WATERMARK] Drawtext filter: {drawtext}")

        # Detect hardware encoder for faster processing
        hw_encoder, hw_preset = detect_hardware_encoder()
        
        if hw_encoder:
            # Use hardware acceleration (GPU encoding)
            print(f"[WATERMARK] Using hardware encoder: {hw_encoder}")
            
            # Build command with hardware encoder
            cmd = [
                'ffmpeg',
                '-hide_banner',
                '-y',
                '-progress', 'pipe:1',  # Enable progress output to stdout
                '-i', input_file,
                '-vf', drawtext,
                '-c:v', hw_encoder,
            ]
            
            # Add encoder-specific quality settings
            if hw_encoder == 'h264_nvenc':
                # NVIDIA NVENC settings
                cmd.extend([
                    '-preset', hw_preset,  # p1 = fastest
                    '-cq', '18',  # Constant quality (equivalent to CRF 18)
                    '-rc', 'vbr',  # Variable bitrate for better quality
                ])
            elif hw_encoder == 'h264_qsv':
                # Intel Quick Sync settings
                cmd.extend([
                    '-preset', hw_preset,  # veryfast
                    '-global_quality', '18',  # Quality level (lower = better)
                ])
            elif hw_encoder == 'h264_amf':
                # AMD AMF settings
                cmd.extend([
                    '-quality', 'quality',  # Quality mode
                    '-rc', 'vbr_latency',  # Variable bitrate
                    '-qp_i', '18',  # I-frame quality
                    '-qp_p', '18',  # P-frame quality
                ])
            
            # Common settings for all hardware encoders
            cmd.extend([
                '-pix_fmt', 'yuv420p',
                '-movflags', '+faststart',
                '-c:a', 'copy',
                output_file
            ])
        else:
            # Fallback to CPU encoding with maximum speed
            print("[WATERMARK] No hardware encoder detected, using CPU encoding")
            cmd = [
                'ffmpeg',
                '-hide_banner',
                '-y',
                '-progress', 'pipe:1',  # Enable progress output to stdout
                '-i', input_file,
                '-vf', drawtext,
                '-c:v', 'libx264',
                '-preset', 'superfast',  # Maximum speed preset (faster than 'faster')
                '-crf', '23',  # Sweet spot for speed/quality (visually lossless)
                '-tune', 'fastdecode',  # Optimize for faster decoding/encoding
                '-x264-params', 'ref=1:bframes=0:me=dia:subme=1:trellis=0:aq-mode=0',  # Extreme speed
                '-pix_fmt', 'yuv420p',
                '-threads', '0',  # Use all available CPU cores
                '-max_muxing_queue_size', '1024',  # Prevent buffer issues
                '-movflags', '+faststart',  # Enable streaming
                '-c:a', 'copy',  # Copy audio without re-encoding
                output_file
            ]
        
        
        print(f"[WATERMARK] FFmpeg command: {' '.join(cmd)}")
        
        # Execute FFmpeg command with progress tracking
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Track progress with updates every 3 seconds
        last_update_time = time.time()
        last_progress_percentage = -1  # Track last percentage to avoid duplicate updates
        progress_percentage = 0
        
        async def read_progress():
            nonlocal progress_percentage, last_update_time, last_progress_percentage
            current_time_us = 0
            
            async for line in process.stdout:
                try:
                    line_str = line.decode('utf-8', errors='ignore').strip()
                    
                    # Parse FFmpeg progress output (format: key=value)
                    if line_str.startswith('out_time_us='):
                        try:
                            # Extract microseconds - handle 'N/A' and other invalid values
                            time_value = line_str.split('=')[1].strip()
                            if time_value == 'N/A' or not time_value:
                                continue  # Skip invalid values
                            
                            current_time_us = int(time_value)
                            current_time_sec = current_time_us / 1000000.0
                            
                            # Calculate percentage
                            if duration_seconds > 0:
                                progress_percentage = min(100, int((current_time_sec / duration_seconds) * 100))
                            
                            # Update status message every 3 seconds AND only if percentage changed
                            current_time = time.time()
                            if status_message and (current_time - last_update_time >= 3.0) and (progress_percentage != last_progress_percentage):
                                try:
                                    await status_message.edit(f"`🎨 Adding watermark... {progress_percentage}% complete`")
                                    last_update_time = current_time
                                    last_progress_percentage = progress_percentage
                                    print(f"[WATERMARK] Progress: {progress_percentage}%")
                                except Exception as e:
                                    # Silently ignore MESSAGE_NOT_MODIFIED errors
                                    if "MESSAGE_NOT_MODIFIED" not in str(e):
                                        print(f"[WATERMARK] Could not update status: {e}")
                        except (ValueError, IndexError) as e:
                            # Skip lines with invalid time values
                            continue
                
                except Exception as e:
                    # Don't spam logs with parsing errors
                    continue
        
        # Start progress tracking task
        progress_task = asyncio.create_task(read_progress())
        
        # Wait for FFmpeg to complete - no timeout, wait as long as needed
        stderr_output = await process.stderr.read()
        await process.wait()
        
        # Wait for progress task to finish
        try:
            await asyncio.wait_for(progress_task, timeout=5)
        except asyncio.TimeoutError:
            pass  # Progress task can timeout, it's okay
        
        # Check if FFmpeg succeeded
        if process.returncode != 0:
            stderr_text = stderr_output.decode('utf-8', errors='ignore')
            print(f"[WATERMARK] ✗ FFmpeg Error (exit code {process.returncode}):")
            print(f"[WATERMARK] stderr: {stderr_text}")
            return False
        
        # Log success
        print(f"[WATERMARK] ✓ Watermark added successfully")
        
        # Verify output file exists
        if os.path.exists(output_file):
            output_size = os.path.getsize(output_file)
            print(f"[WATERMARK] Output file size: {output_size} bytes")
        else:
            print(f"[WATERMARK] ERROR: Output file not created!")
            return False
        
        # Update status at end
        if status_message:
            try:
                await status_message.edit("`✅ Watermark added successfully`")
                await asyncio.sleep(1)  # Brief pause to show success message
            except:
                pass
        
        return True
        
    except Exception as e:
        print(f"[WATERMARK] ✗ Unexpected error adding watermark:")
        print(f"[WATERMARK] Error type: {type(e).__name__}")
        print(f"[WATERMARK] Error message: {e}")
        import traceback
        print(f"[WATERMARK] Traceback:\n{traceback.format_exc()}")
        return False

async def embed_thumbnail(video_file, thumbnail_file, output_file):
    """
    Embed thumbnail image directly into video file
    This ensures Telegram always shows the custom thumbnail
    """
    try:
        # Embed thumbnail as attached picture stream
        cmd = [
            'ffmpeg',
            '-i', video_file,
            '-i', thumbnail_file,
            '-map', '0',  # Map all streams from video
            '-map', '1',  # Map thumbnail image
            '-c', 'copy',  # Copy streams without re-encoding
            '-c:v:1', 'mjpeg',  # Encode thumbnail as MJPEG
            '-disposition:v:1', 'attached_pic',  # Mark as attached picture
            '-y',  # Overwrite
            output_file
        ]
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg Error embedding thumbnail: {e.stderr}")
        return False
    except Exception as e:
        print(f"Error embedding thumbnail: {e}")
        return False

async def extract_thumbnail(input_file, output_thumb, time_seconds=1):
    """
    Extract thumbnail from video at specified time
    """
    try:
        cmd = [
            'ffmpeg',
            '-i', input_file,
            '-ss', str(time_seconds),  # Time in seconds
            '-vframes', '1',  # Extract 1 frame
            '-q:v', '2',  # High quality
            '-y',  # Overwrite
            output_thumb
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        return True
    except Exception as e:
        print(f"Error extracting thumbnail: {e}")
        return False
