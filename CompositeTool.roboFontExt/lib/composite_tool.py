import os
import AppKit
import mojo
from mojo.events import installTool, EditingTool, BaseEventTool, setActiveEventTool
from mojo.drawingTools import *
from mojo.UI import UpdateCurrentGlyphView, CurrentGlyphWindow, GetFile
from defconAppKit.windows.baseWindow import BaseWindowController

from vanilla import *
from glyphConstruction import ParseGlyphConstructionListFromString, GlyphConstructionBuilder
from importlib import reload

import recipee
reload(recipee)


compositeToolBundle = mojo.extensions.ExtensionBundle("CompositeTool")
toolbarIconPath = os.path.join(compositeToolBundle.resourcesPath(), "icon.pdf")
toolbarIcon = AppKit.NSImage.alloc().initWithContentsOfFile_(toolbarIconPath)


glyph_constructor = recipee.glyph_constructor



class SettingsWindow(BaseWindowController):

    def __init__(self):
        self.constructions = glyph_constructor
        
        self.w = FloatingWindow((200, 70), "Window Demo")
        self.w.myButton = SquareButton((10, 10, -10, 20), "Load glyph construction", callback=self.changerecipee)
        self.w.updateComposites = CheckBox((10, 40, -10, 20), 'Update composites', value=True)
        
        self.w.getNSWindow().setStyleMask_(False)
        
        self.w.open()

    def changerecipee(self, sender):    
        root = GetFile(message="Please select a txt file containing glyph construction recipee", title="Select a txt file", allowsMultipleSelection=False, fileTypes=["glyphConstruction", "txt"])
        with open(root, 'r') as file:
            data = file.read()
            
            # Write over existing data
            with open(recipee.__file__, "w") as f:
                f.write(f"glyph_constructor = '''{data}'''")
            
            recipee.glyph_constructor = data
        
        self.constructions = data


class ComponentTool(EditingTool):
    
    def setup(self):
        self.settingsWindow = None

        self.glyph_constructor = self.SettingsWindow.constructions
        self.constructions = ParseGlyphConstructionListFromString(self.SettingsWindow.constructions)
        

    def getToolbarTip(self):
        return 'Component link'

    def getToolbarIcon(self):
        ## return the toolbar icon
        return toolbarIcon

    def becomeActive(self):
        self.SettingsWindow = SettingsWindow()
    
    def becomeInactive(self):
        self.SettingsWindow.w.close()


    def draw(self, viewScale, g=None):
        if g is None:
            g =  self.getGlyph()
        if g is not None:
            save()
            self.updateComp(g, viewScale)
            restore()



    def drawInfos(self, new_x_baseGlyph_anchor, new_y_baseGlyph_anchor, viewScale, glyphView, baseGlyph_anchor):
        color = (1, 0, 0, 1)
        ovalSize = 5 * viewScale

        fill(1, 0, 0, 1)
        stroke(None)
        oval(new_x_baseGlyph_anchor-ovalSize/2, new_y_baseGlyph_anchor-ovalSize/2, ovalSize, ovalSize)

        textAttributes = {
            AppKit.NSFontAttributeName: AppKit.NSFont.systemFontOfSize_(11),
        }

        glyphView.drawTextAtPoint(
            "%s (%d, %d)"%(baseGlyph_anchor.name, new_x_baseGlyph_anchor, new_y_baseGlyph_anchor),
            textAttributes,
            (new_x_baseGlyph_anchor, new_y_baseGlyph_anchor),
            yOffset=-ovalSize-8,
            drawBackground=True,
            centerX=True,
            centerY=True,
            roundBackground=False,
            backgroundXAdd=7,
            backgroundYadd=2)



    def updateRelatedComposites(self, glyph_constructor, cg, cf, new_base_glyph, baseGlyph_anchor, composed_glyph):
        for line in glyph_constructor.split("\n"):
            if len(line) > 0:    
                composed_glyph = line.split("=")[0]
                recipee = line.split("=")[1]
                any_base_glyph = recipee.split("+")[0]

                for diacritic_and_anchor in recipee.split("+")[1:]:
                    new_diacritic = diacritic_and_anchor.split("@")[0]
                    new_anchor = diacritic_and_anchor.split("@")[1]
                    
                    if composed_glyph != cg.name and new_base_glyph == any_base_glyph and new_anchor == baseGlyph_anchor.name and composed_glyph in cf.keys():
                        constructionGlyph = GlyphConstructionBuilder(line, cf)

                        new_glyph = cf.newGlyph(constructionGlyph.name, clear=True)

                        # get the destination glyph in the font
                        new_glyph = cf.newGlyph(constructionGlyph.name, clear=True)

                        # draw the construction glyph into the destination glyph
                        constructionGlyph.draw(new_glyph.getPen())

                        new_glyph.changed()


    def updateComp(self, g, viewScale):
        
        if len(g.selectedComponents) == 1:
            cf = g.font
            cg = g
            selected_component = cg.selectedComponents[0]
            selected_component_name = cg.selectedComponents[0].baseGlyph
            
            constructions = self.constructions
            glyph_constructor = self.glyph_constructor
                        
            glyphWindow = CurrentGlyphWindow()
            glyphView = glyphWindow.getGlyphView()
            if not glyphWindow:
                return


            
            for line in glyph_constructor.split("\n"):
                if len(line) > 0:    
                    composed_glyph = line.split("=")[0]
                    recipee = line.split("=")[1]
                    new_base_glyph = recipee.split("+")[0]
                    
                    if new_base_glyph == cg.components[0].baseGlyph and cg.name == composed_glyph:
                        
                        construction = f"{composed_glyph}={recipee}"
                        constructionGlyph = GlyphConstructionBuilder(construction, cf)
            
                        if constructionGlyph.name == cg.name:
                            for component_index, c in enumerate(constructionGlyph.components):
                                c = list(c)[0]
                        
                                if c == selected_component_name:
                                    baseGlyphName = constructionGlyph.components[component_index-1][0]
                                    baseGlyph = cf[baseGlyphName]
                            
                                    recipee = construction.split("=")[1]
                            
                                    for diacritic_and_anchor in recipee.split("+")[1:]:
                                        diacritic = diacritic_and_anchor.split("@")[0]
                                        anchor = diacritic_and_anchor.split("@")[1]
                                
                                        if diacritic == selected_component_name:
                                            selected_component_anchor_name = "_%s"%anchor
                                    
                                            for baseGlyph_anchor in baseGlyph.anchors:
                                                if baseGlyph_anchor.name == anchor:
                                                    x_baseGlyph_anchor = baseGlyph_anchor.x
                                                    y_baseGlyph_anchor = baseGlyph_anchor.y
                                            
                                                    selected_comp_baseGlyph = cf[selected_component_name]
                                            
                                                    for selectedComponent_anchor in selected_comp_baseGlyph.anchors:
                                                        if selected_component_anchor_name == selectedComponent_anchor.name:
                                                    
                                                            x_offset = 0
                                                            y_offset = 0
                                                            for previous_components in constructionGlyph.components[1:component_index]:
                                                                for cg_component in cg.components:
                                                                    if cg_component.baseGlyph == previous_components[0]:
                                                                        x_offset += cg_component.offset[0]
                                                                        y_offset += cg_component.offset[1]
                                                    

                                                            new_x_baseGlyph_anchor = selectedComponent_anchor.x + selected_component.offset[0] - x_offset
                                                            new_y_baseGlyph_anchor = selectedComponent_anchor.y + selected_component.offset[1] - y_offset
                                                            
                                                            
                                                            self.drawInfos(new_x_baseGlyph_anchor, new_y_baseGlyph_anchor, viewScale, glyphView, baseGlyph_anchor)

                                                    
                                                            ### Update baseGlyph anchor
                                                            baseGlyph_anchor.x = new_x_baseGlyph_anchor
                                                            baseGlyph_anchor.y = new_y_baseGlyph_anchor
                                                    

                                                            if self.SettingsWindow.w.updateComposites.get() == 1:
                                                                self.updateRelatedComposites(glyph_constructor, cg, cf, new_base_glyph, baseGlyph_anchor, composed_glyph)



                                    
            
installTool(ComponentTool())

