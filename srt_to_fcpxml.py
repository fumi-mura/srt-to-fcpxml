import re
import xml.etree.ElementTree as ET
from datetime import datetime
import argparse

FRAME_RATE = 30  # 30fps


def srt_time_to_frames(srt_time):
    h, m, s_ms = srt_time.split(':')
    s, ms = s_ms.split(',')
    total_seconds = int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000
    return round(total_seconds * FRAME_RATE)


def parse_srt(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    blocks = re.split(r'\n\n+', content.strip())
    subtitles = []

    for block in blocks:
        lines = block.strip().splitlines()
        if len(lines) >= 3:
            times = lines[1]
            start_time, end_time = times.split(' --> ')
            text = '\n'.join(lines[2:])
            start_frame = srt_time_to_frames(start_time.strip())
            end_frame = srt_time_to_frames(end_time.strip())
            duration = end_frame - start_frame

            subtitles.append({
                'offset': f"{start_frame}/{FRAME_RATE}s",
                'start': "0s",
                'duration': f"{duration}/{FRAME_RATE}s",
                'text': text
            })

    return subtitles


def create_fcpxml(subtitles, output_path):
    ET.register_namespace('', "http://www.apple.com/fcpxml")

    fcpxml = ET.Element("fcpxml", version="1.10")

    resources = ET.SubElement(fcpxml, "resources")
    ET.SubElement(resources, "format", id="r1", name="FFVideoFormat1080p30", frameDuration="1/30s")
    ET.SubElement(resources, "effect", id="r2", name="Basic Title", uid=".../Titles.localized/Bumper:Opener.localized/Basic Title.localized/Basic Title.moti")

    library = ET.SubElement(fcpxml, "library")
    event = ET.SubElement(library, "event", name="Subtitles")
    project = ET.SubElement(event, "project", name="SRT Import")
    sequence = ET.SubElement(project, "sequence", format="r1", duration="60s", tcStart="0s", tcFormat="NDF")
    spine = ET.SubElement(sequence, "spine")

    for i, sub in enumerate(subtitles):
        title = ET.SubElement(spine, "title", name=f"Subtitle {i+1}",
                              lane="1",
                              offset=sub['offset'],
                              start=sub['start'],
                              duration=sub['duration'],
                              ref="r2")
        text_element = ET.SubElement(title, "text")
        text_element.text = sub["text"]

    tree = ET.ElementTree(fcpxml)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)
    print(f"✅ FCPXMLを書き出しました: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert .srt to Final Cut Pro .fcpxml")
    parser.add_argument("srt_file", help="Path to the input .srt file")
    args = parser.parse_args()

    today = datetime.now().strftime("%Y%m%d")
    output_file = f"./outputs/{today}_outputs.fcpxml"

    subtitles = parse_srt(args.srt_file)
    create_fcpxml(subtitles, output_file)
