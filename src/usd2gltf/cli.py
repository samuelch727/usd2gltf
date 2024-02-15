import argparse
import sys
import logging
import converter as converter
from pxr import Usd, UsdShade, Sdf

def preprocess_usd_stage_for_gltf_conversion(stage):
    # Iterate over all materials in the stage
    for prim in stage.Traverse():
        if prim.IsA(UsdShade.Material):
            material = UsdShade.Material(prim)
            
            # Ensure the material's 'frame:stPrimvarName' input exists and set it to 'st'
            stInput = material.GetInput('frame:stPrimvarName')
            if not stInput:
                stInput = material.CreateInput('frame:stPrimvarName', Sdf.ValueTypeNames.Token)
            stInput.Set('st')
                
            # Define or find the UsdPrimvarReader_float2 shader for 'st' reading
            stReaderPath = prim.GetPath().AppendChild("stReader")
            stReader = UsdShade.Shader.Define(stage, stReaderPath)
            stReader.CreateIdAttr('UsdPrimvarReader_float2')
                
            # Set the 'varname' input of the reader to 'st'
            varnameInput = stReader.CreateInput('varname', Sdf.ValueTypeNames.Token)
            varnameInput.Set('st')
                
            # Correctly connect the material's 'st' input to the PrimvarReader's output
            resultOutput = stReader.CreateOutput('result', Sdf.ValueTypeNames.Float2)
            stInput.ConnectToSource(resultOutput)

            print(f"Configured 'st' primvar reader for material: {prim.GetPath()}")



def run(args):
    print("Converting: {0}\nTo: {1}".format(args.input, args.output))
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    factory = converter.Converter()
    factory.interpolation = args.interpolation
    factory.flatten_xform_animation = args.flatten

    stage = factory.load_usd(args.input)
    preprocess_usd_stage_for_gltf_conversion(stage)
    factory.process(stage, args.output)

    print("Converted!")


def main():
    parser = argparse.ArgumentParser(
        description="Convert incoming USD(z) file to glTF/glb"
    )
    parser.add_argument(
        "-i",
        "--input",
        dest="input",
        action="store",
        help="Input USD (.usd, .usdc, .usda, .usdz)",
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="output",
        action="store",
        help="Output glTF (.gltf, .glb)",
    )

    parser.add_argument(
        "--interpolation",
        dest="interpolation",
        action="store",
        default="LINEAR",
        help="Interpolation of animation (LINEAR, STEP, CUBIC)",
    )

    parser.add_argument(
        "-d",
        "--debug",
        dest="debug",
        action="store_true",
        default=False,
        help="Run in debug mode",
    )

    parser.add_argument(
        "-f",
        "--flatten",
        dest="flatten",
        action="store_true",
        default=False,
        help="Flatten all animations into one animation",
    )

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    parser.set_defaults(func=run)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()


