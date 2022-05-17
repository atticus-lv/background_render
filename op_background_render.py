import os
import bpy
from bpy.props import EnumProperty, BoolProperty, StringProperty, IntProperty, FloatProperty


def get_cmd(self, context):
    blender_path = bpy.app.binary_path.replace("\\", "/")
    filepath = bpy.data.filepath.replace("\\", "/")
    output_path = bpy.path.abspath(self.filepath)

    cmd = [
        'start',
        blender_path,
        '--factory-startup',
        '-b',
        filepath
    ]

    # set output path
    cmd.append('-o')
    cmd.append(output_path)

    if self.operator_type == 'STILL':
        cmd.append('-f')
        cmd.append(f'{self.frame_current}')

    elif self.operator_type == 'ANIM':
        if not self.use_scene_frame_range:
            cmd.append(f'--frame-start {self.frame_start}')
            cmd.append(f'--frame-end {self.frame_end}')

        cmd.append('-a')

    return ' '.join(cmd)


def generate_file(self, context):
    if self.generate_batch_file is False:
        return

    cmd = get_cmd(self, context)

    name = os.path.basename(bpy.data.filepath[:-6])
    dir = os.path.dirname(bpy.data.filepath)

    frame = self.frame_current if self.operator_type == 'STILL' else str(
        self.frame_start) + '-' + str(self.frame_end)

    path = os.path.join(dir,
                        f"{name}_{self.operator_type.title()}_frame_{frame}.bat")

    with open(path, 'w') as f:
        f.write(cmd)
    # open folder
    bpy.ops.wm.path_open(filepath=dir)
    # make it looks like an operator clicking
    self.generate_batch_file = False


class WM_OT_background_render(bpy.types.Operator):
    """Ctrl click to set options for background render"""
    bl_idname = "wm.background_render"
    bl_label = "Background Render"
    bl_options = {'INTERNAL'}

    # properties
    operator_type: EnumProperty(name='Type', items=[
        ('STILL', 'Image', 'Render Image', 'RENDER_STILL', 0),
        ('ANIM', 'Animation', 'Render Animation', 'RENDER_ANIMATION', 1),
    ], default='STILL')

    use_current_frame: BoolProperty(name='Use Current Frame', default=True)
    frame_current: IntProperty(name='Frame', default=1)

    use_scene_frame_range: BoolProperty(name='Use Scene Frame Range', default=True)
    frame_start: IntProperty(name='Start Frame', default=1)
    frame_end: IntProperty(name='End Frame', default=250)

    use_scene_filepath: BoolProperty(name='Use Scene Filepath', default=True)
    filepath: StringProperty(name='Filepath', default='//render/image', subtype='FILE_PATH')

    generate_batch_file: BoolProperty(name='Generate Batch File (.bat)', update=generate_file)

    # action
    open_dir: BoolProperty(name='Open Directory', default=False)
    # data
    cmd = None

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        layout.prop(self, "operator_type", expand=True)

        if self.operator_type == 'STILL':
            col = layout.column(align=True)
            col.prop(self, "use_current_frame")
            if not self.use_current_frame:
                col.prop(self, "frame_current")
        elif self.operator_type == 'ANIM':
            col = layout.column(align=True)
            col.prop(self, "use_scene_frame_range")
            if not self.use_scene_frame_range:
                col.prop(self, "frame_start")
                col.prop(self, "frame_end")

        layout.prop(self, "use_scene_filepath")
        if not self.use_scene_filepath:
            layout.prop(self, "filepath")

        layout.separator(factor=0.5)
        box = layout.box()
        box.prop(self, "open_dir")
        box.prop(self, "generate_batch_file", icon='FILE_NEW', toggle=True)

    def invoke(self, context, event):
        self.cmd = None
        if bpy.data.filepath == '' or bpy.data.is_dirty:
            self.report({'ERROR'}, "Save the current Blender file")
            return {'FINISHED'}
        # insert current setting to clean flow code
        self.frame_current = context.scene.frame_current
        self.frame_start = context.scene.frame_start
        self.frame_end = context.scene.frame_end
        self.filepath = context.scene.render.filepath

        if not event.ctrl:  # ctrl to popup settings
            return self.execute(context)

        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        cmd = get_cmd(self, context)
        dir = bpy.path.abspath(os.path.dirname(self.filepath))
        # make a dir if not exists
        if not os.path.exists(dir):
            os.makedirs(dir)
        # open this dir
        if self.open_dir:
            bpy.ops.wm.path_open(filepath=dir)

        os.system(cmd)

        return {'FINISHED'}


def draw_render_properties(self, context):
    layout = self.layout

    box = layout.box()
    box.use_property_split = True

    box.label(text='Background Render')
    row = box.row()
    row.scale_y = 1.2
    row.operator("wm.background_render", icon='RENDER_STILL', text='Render Image').operator_type = 'STILL'
    row.operator("wm.background_render", icon='RENDER_ANIMATION', text='Render Animation').operator_type = 'ANIM'


def register():
    bpy.utils.register_class(WM_OT_background_render)
    bpy.types.RENDER_PT_context.append(draw_render_properties)


def unregister():
    bpy.utils.unregister_class(WM_OT_background_render)
    bpy.types.RENDER_PT_context.remove(draw_render_properties)
