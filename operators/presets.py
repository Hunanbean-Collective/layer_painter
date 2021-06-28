import bpy
from . import operator_utils
from .. import constants
from .. import utils


class LP_OT_PbrSetup(bpy.types.Operator):
    bl_idname = "lp.pbr_setup"
    bl_label = "Add PBR channels"
    bl_description = "Adds the basic PBR channels to your material"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    material: bpy.props.StringProperty(name="Material",
                                       description="Name of the material to use",
                                       options={"HIDDEN", "SKIP_SAVE"})

    @classmethod
    def poll(cls, context):
        return operator_utils.base_poll(context)

    def add_missing(self, mat, princ, bump, out):
        if not out:
            out = mat.node_tree.nodes.new(constants.NODES["OUT"])
        if not princ:
            princ = mat.node_tree.nodes.new(constants.NODES["PRINC"])
            princ.location = (out.location[0]-200, out.location[1])
        if not princ.outputs[0].is_linked:
            mat.node_tree.links.new(princ.outputs[0], out.inputs[0])
        if not bump:
            bump = mat.node_tree.nodes.new(constants.NODES["BUMP"])
            bump.location = (princ.location[0], princ.location[1]-630)
        if not bump.outputs[0].is_linked:
            mat.node_tree.links.new(bump.outputs[0], princ.inputs["Normal"])
        return princ, bump, out

    def get_nodes(self, mat):
        princ, bump, out = None, None, None
        for node in mat.node_tree.nodes:
            if node.bl_idname == constants.NODES["PRINC"]:
                princ = node
            elif node.bl_idname == constants.NODES["BUMP"]:
                bump = node
            elif node.bl_idname == constants.NODES["OUT"]:
                out = node
        return self.add_missing(mat, princ, bump, out)

    def execute(self, context):
        mat = bpy.data.materials[self.material]
        princ, bump, _ = self.get_nodes(mat)

        color = mat.lp.add_channel(princ.inputs["Base Color"])
        color.default_enable = True
        channel = mat.lp.add_channel(princ.inputs["Roughness"])
        channel = mat.lp.add_channel(princ.inputs["Metallic"])
        channel = mat.lp.add_channel(princ.inputs["Emission"])
        channel = mat.lp.add_channel(bump.inputs["Normal"])
        channel.name = "Normal"
        channel = mat.lp.add_channel(bump.inputs["Height"])
        channel.name = "Height"

        if len(mat.lp.layers) == 1:
            mat.lp.layers[0].get_channel_node(color.uid).mute = False

        utils.redraw()
        return {"FINISHED"}
