"""Generate MicroPython bindings through the upstream uprotobuf plugin."""
import sys
import tempfile
from pathlib import Path

from grpc_tools import protoc
from google.protobuf import descriptor_pb2
from google.protobuf.compiler import plugin_pb2

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import uprotobuf_plugin


def main():
    with tempfile.TemporaryDirectory(dir=ROOT) as folder:
        descriptor = Path(folder) / "temperature.pb"
        result = protoc.main([
            "protoc", "-I" + str(ROOT),
            "--descriptor_set_out=" + str(descriptor),
            str(ROOT / "temperature.proto")])
        if result:
            raise RuntimeError("protoc failed")
        descriptors = descriptor_pb2.FileDescriptorSet.FromString(
            descriptor.read_bytes())
    request = plugin_pb2.CodeGeneratorRequest()
    request.file_to_generate.append("temperature.proto")
    request.proto_file.extend(descriptors.file)
    response = plugin_pb2.CodeGeneratorResponse()
    uprotobuf_plugin.generateCode(request, response)
    for file in response.file:
        (ROOT / file.name).write_text(file.content, encoding="utf-8")
        print("Generated", file.name)


if __name__ == "__main__":
    main()

