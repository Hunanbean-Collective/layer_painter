import bpy
from .. import utils
from . import group_utils
from .layer import LP_LayerProperties
from .channel import LP_ChannelProperties


class LP_MaterialProperties(bpy.types.PropertyGroup):
    
    ### Properties of the material
    
    @property
    def mat(self):
        return self.id_data
    
    
    @property
    def ntree(self):
        return self.mat.node_tree
    
    
    uid: bpy.props.StringProperty(name="UID",
                                  description="UID of this material. Empty if it hasn't been used by LP yet",
                                  default="")
    
    
    @property
    def active(self):
        if self.selected < len(self.layers):
            return self.layers[self.selected]
        return None
    
    
    @property
    def layer_nodes(self):
        return [layer.node for layer in self.layers]
    
    
    layers: bpy.props.CollectionProperty(type=LP_LayerProperties)


    selected: bpy.props.IntProperty(name="Selected Layer",
                                    description="Index of the selected layer",
                                    min=0,
                                    default=0)
    
    
    ### Methods to manipulate the layers of this material
    
    @property
    def has_faulty_layers(self):
        """ returns a boolean saying if there are any layers without a node """
        for layer in self.layers:
            if not layer.node:
                return True
        return False
            
            
    def layer_index(self, layer):
        """ returns the index of the given layer """
        for i in range( len(self.layers) ):
            if self.layers[i].uid == layer.uid:
                return i
        return -1
            
            
    def layer_uid_index(self, uid):
        """ returns the index of the given layer uid """
        for i in range( len(self.layers) ):
            if self.layers[i].uid == uid:
                return i
        return -1
            
            
    def layer_by_uid(self, uid):
        """ returns the layer with the given uid """
        for layer in self.layers:
            if layer.uid == uid:
                return layer
        return None
    
    
    def layer_above(self, layer, amount=1):
        """ returns the layer which is the given amount above the given layer or None if out of range """
        index = self.layer_index(layer)
        if index+amount < len(self.layers):
            return self.layers[ index+amount ]
        return None
    
    
    def layer_below(self, layer, amount=1):
        """ returns the layer which is the given amount below the given layer or None if out of range """
        index = self.layer_index(layer)
        if index-amount < len(self.layers) and index-amount >= 0:
            return self.layers[ index-amount ]
        return None
    
    
    def layers_around(self, layer, amount=1):
        """ returns the layer above and below the given layer """
        return self.layer_below(layer, amount), self.layer_above(layer, amount)
    
    
    def __add_any_layer(self, layer_type):
        """ method to add a layer of any type above the active layer in this material """
        _, ngroup = group_utils.make_group(self.ntree, utils.get_unique_name(self.layer_nodes, "Layer", ".", "label"))

        self.layers.add()
        self.layers.move( len(self.layers)-1, self.selected+1 )
        
        if len(self.layers) > 1:
            self.selected += 1

        layer = self.layers[ self.selected ]
        layer.init(ngroup, layer_type, self.uid)
                
                
    def add_fill_layer(self):
        """ adds a fill layer above the active layer to this material """
        self.__add_any_layer("FILL")
                
                
    def add_paint_layer(self):
        """ adds a paint layer above the active layer to this material """
        self.__add_any_layer("PAINT")
        
        
    def remove_active_layer(self):
        """ removes the active layer from this material """
        below = self.layer_below( self.active )
        
        if self.active.node:
            ntree = self.active.node.node_tree
            self.mat.node_tree.nodes.remove( self.active.node )
            bpy.data.node_groups.remove( ntree )
        
        self.layers.remove( self.selected )
        self.selected -= 1
        
        if below and below.node:
            below.connect_channel_outputs()
        
        
    def move_active_layer_up(self):
        """ moves the active layer up one spot """
        if self.active:            
            self.layers.move( self.selected, self.selected+1 )
            self.selected += 1

            self.active.move_up()
    
    
    def move_active_layer_down(self):
        """ moves the active layer down one spot """
        if self.active:
            self.layers.move( self.selected, self.selected-1 )
            self.selected -= 1

            self.active.move_down()
            
    
    def get_channel_data_type(self, layer, channel_uid):
        """ returns the type of data that this channel is set to for the given layer
        return in ("COL", "TEX")
        """
        return layer.get_channel_data_type( channel_uid )
    
    
    def cycle_channel_data_type(self, layer, channel_uid):
        """ cycles the data that this channel is set to for the given layer """
        layer.cycle_channel_data_type( channel_uid )
        
    
    ### Methods to manipulate the channels of this material
    
    channels: bpy.props.CollectionProperty(type=LP_ChannelProperties)
    
    
    @property
    def has_faulty_channels(self):
        """ returns a boolean saying if there are any channels without a node """
        for channel in self.channels:
            if not channel.inp:
                return True
        return False
    
    
    @property
    def channel_uids(self):
        return [channel.uid for channel in self.channels]
    
    
    def channel_by_inp(self, inp):
        """ returns the channel properties matching the given input """
        for channel in self.channels:
            if hasattr(inp, "uid") and channel.uid == inp.uid:
                return channel
    
    
    def channel_by_uid(self, uid):
        """ returns the channel properties matching the given uid """
        for channel in self.channels:
            if channel.uid == uid:
                return channel
            
            
    def channel_index(self, channel):
        """ returns the index of the given channel """
        for i in range(len(self.channels)):
            if self.channels[i].uid == channel.uid:
                return i
        return -1
    

    def __update_layer_channels(self):
        """ updates all channel in and outputs on all layers in this material """
        for layer in self.layers:
            layer.setup_channels()
    
    
    def add_channel(self, inp):
        """ adds a channel for the given input """
        channel = self.channels.add()
        channel.init(inp, self.uid)
        
        self.__update_layer_channels()
        
        return channel
        
        
    def remove_channel(self, inp):
        """ removes the channel for the given input """
        if type(inp) == str:
            channel = self.channel_by_uid(inp)
        else:
            channel = self.channel_by_inp(inp)

        index = self.channel_index(channel)
        
        channel.disable()
        self.channels.remove( index )
        
        self.__update_layer_channels()
        
        
    def move_channel_up(self, uid):
        """ moves the given channel up one spot """
        channel = self.channel_by_uid( uid )
        index = self.channel_index( channel )

        if channel != self.channels[0]:
            self.channels.move( index, index-1 )
    
    
    def move_channel_down(self, uid):
        """ moves the given channel down one spot """
        channel = self.channel_by_uid( uid )
        index = self.channel_index( channel )

        if channel != self.channels[-1]:
            self.channels.move( index, index+1 )