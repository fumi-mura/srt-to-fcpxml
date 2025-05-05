import re
import xml.etree.ElementTree as ET
from datetime import datetime
import argparse
import os

FRAME_RATE = 30  # 30fps


def srt_time_to_seconds(srt_time):
    """Convert SRT timestamp to seconds"""
    h, m, s_ms = srt_time.split(':')
    s, ms = s_ms.split(',')
    total_seconds = int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000
    return total_seconds


def parse_srt(file_path):
    """Parse SRT file and extract subtitle information"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    blocks = re.split(r'\n\n+', content.strip())
    subtitles = []

    for i, block in enumerate(blocks):
        lines = block.strip().splitlines()
        if len(lines) >= 3:
            try:
                times = lines[1]
                start_time, end_time = times.split(' --> ')
                text = '\n'.join(lines[2:])
                
                # Calculate time values in seconds
                start_seconds = srt_time_to_seconds(start_time.strip())
                end_seconds = srt_time_to_seconds(end_time.strip())
                duration_seconds = end_seconds - start_seconds
                
                # Calculate frames
                start_frames = int(start_seconds * FRAME_RATE)
                duration_frames = int(duration_seconds * FRAME_RATE)
                
                # Format for FCPXML
                offset = f"{start_frames}/30s"
                duration = f"{duration_frames}/30s"
                
                subtitles.append({
                    'number': i + 1,
                    'offset': offset,
                    'start': "0s",
                    'duration': duration,
                    'text': text
                })
            except Exception as e:
                print(f"Error parsing subtitle block {i+1}: {e}")
                continue

    return subtitles


def create_fcpxml_string(subtitles):
    """Create FCPXML content as a string to ensure exact format matching"""
    xml_header = '<?xml version="1.0" encoding="utf-8"?>\n'
    fcpxml_start = '<fcpxml version="1.10">'
    
    # Build resources section
    resources = '<resources>'
    resources += '<format id="r1" name="FFVideoFormat1080p30" frameDuration="1/30s" />'
    resources += '<effect id="r2" name="Basic Title" uid=".../Titles.localized/Bumper:Opener.localized/Basic Title.localized/Basic Title.moti" />'
    resources += '</resources>'
    
    # Build library structure
    library = '<library>'
    library += '<event name="Subtitles">'
    library += '<project name="SRT Import">'
    library += '<sequence format="r1" duration="60s" tcStart="0s" tcFormat="NDF">'
    library += '<spine>'
    
    # Add each subtitle
    for sub in subtitles:
        title_start = f'<title name="Subtitle {sub["number"]}" lane="1" offset="{sub["offset"]}" start="{sub["start"]}" duration="{sub["duration"]}" ref="r2">'
        text_element = f'<text>{sub["text"]}</text>'
        title_end = '</title>'
        library += title_start + text_element + title_end
    
    # Close tags
    library += '</spine></sequence></project></event></library>'
    
    fcpxml_end = '</fcpxml>'
    
    # Combine all parts
    return xml_header + fcpxml_start + resources + library + fcpxml_end


def write_fcpxml(xml_string, output_path):
    """Write XML string to file"""
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(xml_string)
    
    print(f"✅ FCPXML exported to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Convert .srt to Final Cut Pro .fcpxml")
    parser.add_argument("srt_file", help="Path to the input .srt file")
    parser.add_argument("-o", "--output", help="Path to the output .fcpxml file (optional)")
    parser.add_argument("-f", "--framerate", type=int, default=30, help="Frame rate (default: 30)")
    args = parser.parse_args()
    
    global FRAME_RATE
    FRAME_RATE = args.framerate
    
    # Set default output path if not specified
    if not args.output:
        today = datetime.now().strftime("%Y%m%d")
        output_dir = "./outputs"
        os.makedirs(output_dir, exist_ok=True)
        output_file = f"{output_dir}/{today}_output.fcpxml"
    else:
        output_file = args.output
    
    subtitles = parse_srt(args.srt_file)
    xml_string = create_fcpxml_string(subtitles)
    write_fcpxml(xml_string, output_file)


if __name__ == "__main__":
    main()
