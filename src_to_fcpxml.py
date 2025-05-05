import re
import xml.etree.ElementTree as ET
from datetime import timedelta


def srt_time_to_fcpxml_time(srt_time):
    """SRT時間形式をFCPXML形式の時間に変換"""
    h, m, s_ms = srt_time.split(":")
    s, ms = s_ms.split(",")
    total_seconds = int(h) * 3600 + int(m) * 60 + int(s)
    return f"{total_seconds}.{ms}s"


def parse_srt(file_path):
    """SRTファイルを解析して、字幕リストを返す"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    blocks = re.split(r'\n\n+', content.strip())
    subtitles = []
    for block in blocks:
        lines = block.strip().splitlines()
        if len(lines) >= 3:
            index = lines[0]
            times = lines[1]
            text = "\n".join(lines[2:])
            start, end = times.split(" --> ")
            subtitles.append({
                "start": srt_time_to_fcpxml_time(start.strip()),
                "end": srt_time_to_fcpxml_time(end.strip()),
                "text": text
            })
    return subtitles


def create_fcpxml(subtitles, output_path="output.fcpxml"):
    """FCPXMLファイルを作成する"""
    ET.register_namespace('', "http://www.apple.com/fcpxml")

    fcpxml = ET.Element("fcpxml", version="1.10")
    resources = ET.SubElement(fcpxml, "resources")
    format_elem = ET.SubElement(resources, "format", id="r1", name="FFVideoFormat1080p30", frameDuration="1/30s")
    project = ET.SubElement(fcpxml, "library")
    event = ET.SubElement(project, "event", name="Subtitles")
    project_elem = ET.SubElement(event, "project", name="SRT Import")
    sequence = ET.SubElement(project_elem, "sequence", format="r1", duration="60s")
    spine = ET.SubElement(sequence, "spine")

    for i, sub in enumerate(subtitles):
        title = ET.SubElement(spine, "title", name=f"Subtitle {i+1}",
                              lane="1", offset=sub["start"], start=sub["start"], duration=sub["end"])
        ET.SubElement(title, "text").text = sub["text"]

    tree = ET.ElementTree(fcpxml)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)
    print(f"FCPXMLを書き出しました: {output_path}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="SRT to FCPXML converter")
    parser.add_argument("srt_file", help="Path to input .srt file")
    parser.add_argument("output_file", nargs="?", default="output.fcpxml", help="Output .fcpxml file path")
    args = parser.parse_args()

    subtitles = parse_srt(args.srt_file)
    create_fcpxml(subtitles, args.output_file)
