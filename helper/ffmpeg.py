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
        # Normalize and use absolute paths for Windows stability
        input_file = os.path.abspath(input_file).replace("\\", "/")
        output_file = os.path.abspath(output_file).replace("\\", "/")
        
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

        # Calculate consistent font size based on video height
        fontsize = max(20, int(height * 0.035))
        fontsize = min(60, max(20, fontsize))
        print(f"[WATERMARK] Calculated font size: {fontsize}")

        # Get duration for scrolling watermark
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
        
        # Calculate watermark position formula
        if position == "scroll-lr-center":
            d = duration_seconds if duration_seconds > 0 else 1.0
            x = f"(W-text_w)*t/{d}"
            y = f"(H-text_h)/2"
        elif position == "top-left":
            x = "10"
            y = "10"
        elif position == "top-right":
            x = "W-w-10"
            y = "10"
        elif position == "bottom-left":
            x = "10"
            y = "H-h-10"
        elif position == "bottom-right":
            x = "W-w-10"
            y = "H-h-10"
        else:  # center
            x = "(W-w)/2"
            y = "(H-h)/2"
        
        print(f"[WATERMARK] Position formula - x: {x}, y: {y}")
        
        # Font file detection with Windows support
        fontfile_candidates = [
            os.environ.get("WATERMARK_FONTFILE", ""),
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/times.ttf",
            "C:/Windows/Fonts/calibri.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ]
        
        fontfile = None
        for candidate in fontfile_candidates:
            if candidate and os.path.exists(candidate):
                fontfile = candidate
                print(f"[WATERMARK] ✓ Found font file: {fontfile}")
                break
        
        if not fontfile:
            print("[WATERMARK] WARNING: No font file found, FFmpeg will use system default")
            fontfile_ffmpeg = ""
        else:
            fontfile_ffmpeg = fontfile.replace("\\", "/").replace(":", "\\:")

        # Basic escaping for drawtext
        escaped_text = watermark_text.replace("\\", "\\\\").replace("'", "\\'").replace(":", "\\:")
        box_border = max(3, int(fontsize * 0.15))

        # Build drawtext filter
        drawtext_parts = [f"text='{escaped_text}'", f"fontcolor=white@0.9", f"fontsize={fontsize}", f"x={x}", f"y={y}", f"box=1", f"boxcolor=black@0.5", f"boxborderw={box_border}"]
        if fontfile_ffmpeg:
            drawtext_parts.insert(0, f"fontfile='{fontfile_ffmpeg}'")
        
        drawtext = f"drawtext=" + ":".join(drawtext_parts)
        print(f"[WATERMARK] Drawtext filter: {drawtext}")

        # Detect hardware encoder
        hw_encoder, hw_preset = detect_hardware_encoder()
        
        # Preparation for retry logic
        attempts = []
        if hw_encoder:
            # First attempt with hardware encoder
            hw_cmd = [
                'ffmpeg', '-hide_banner', '-y', '-progress', 'pipe:1',
                '-i', input_file,
                '-vf', drawtext,
                '-c:v', hw_encoder
            ]
            
            if hw_encoder == 'h264_nvenc':
                hw_cmd.extend(['-preset', hw_preset, '-cq', '18', '-rc', 'vbr'])
            elif hw_encoder == 'h264_qsv':
                # Explicitly set pix_fmt for QSV to avoid crash/warnings
                hw_cmd.extend(['-preset', hw_preset, '-global_quality', '18', '-pix_fmt', 'nv12'])
            elif hw_encoder == 'h264_amf':
                hw_cmd.extend(['-quality', 'quality', '-rc', 'vbr_latency', '-qp_i', '18', '-qp_p', '18'])
            
            hw_cmd.extend(['-movflags', '+faststart', '-c:a', 'copy', output_file])
            attempts.append(("Hardware Acceleration", hw_cmd))

        # Always add CPU fallback (or primary if no HW encoder)
        cpu_cmd = [
            'ffmpeg', '-hide_banner', '-y', '-progress', 'pipe:1',
            '-i', input_file,
            '-vf', drawtext,
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-crf', '28',
            '-pix_fmt', 'yuv420p',
            '-movflags', '+faststart',
            '-c:a', 'copy',
            output_file
        ]
        attempts.append(("CPU Encoding (High Speed)", cpu_cmd))

        # Execute with retry logic
        for attempt_name, cmd in attempts:
            print(f"[WATERMARK] Attempting with {attempt_name}...")
            print(f"[WATERMARK] FFmpeg command: {' '.join(cmd)}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Progress tracking
            last_update_time = time.time()
            last_progress_percentage = -1
            progress_percentage = 0
            
            async def read_progress():
                nonlocal progress_percentage, last_update_time, last_progress_percentage
                async for line in process.stdout:
                    try:
                        line_str = line.decode('utf-8', errors='ignore').strip()
                        if line_str.startswith('out_time_us='):
                            time_value = line_str.split('=')[1].strip()
                            if time_value == 'N/A' or not time_value: continue
                            
                            current_time_sec = int(time_value) / 1000000.0
                            if duration_seconds > 0:
                                progress_percentage = min(100, int((current_time_sec / duration_seconds) * 100))
                            
                            c_time = time.time()
                            if status_message and (c_time - last_update_time >= 3.0) and (progress_percentage != last_progress_percentage):
                                try:
                                    await status_message.edit(f"`🎨 Adding watermark ({attempt_name})... {progress_percentage}%`")
                                    last_update_time = c_time
                                    last_progress_percentage = progress_percentage
                                except: pass
                    except: continue

            progress_task = asyncio.create_task(read_progress())
            stderr_output = await process.stderr.read()
            await process.wait()
            
            try: await asyncio.wait_for(progress_task, timeout=2)
            except: pass
            
            if process.returncode == 0 and os.path.exists(output_file) and os.path.getsize(output_file) > 1000:
                print(f"[WATERMARK] ✓ Success with {attempt_name}")
                if status_message:
                    try: await status_message.edit("`✅ Watermark added successfully`")
                    except: pass
                return True
            
            # If we're here, this attempt failed
            stderr_text = stderr_output.decode('utf-8', errors='ignore')
            print(f"[WATERMARK] ✗ {attempt_name} failed (code {process.returncode})")
            print(f"[WATERMARK] stderr: {stderr_text[:500]}...")
            
            if attempt_name == attempts[-1][0]:
                # Last attempt failed
                return False
            else:
                print(f"[WATERMARK] Retrying with next method...")
                if status_message:
                    try: await status_message.edit("`⚠️ Primary method failed, retrying...`")
                    except: pass
                await asyncio.sleep(1)

        return False
        
    except Exception as e:
        print(f"[WATERMARK] ✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
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
