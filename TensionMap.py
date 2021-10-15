"""
This plugin was ported to python from C++,
All credits by Anno Schachner
original plugin is here https://github.com/wiremas/tension

Ported by Alexander Smirnov
https://vimeo.com/315989835
https://gist.github.com/Onefabis/57a4f9fe9eb1686505bbe6297d675671

Modified by davidlatwe

"""

import sys
import maya.api.OpenMaya as om2
import maya.OpenMaya as om

kPluginNodeName = "tensionMap"
origAttrName = "orig"
deformedAttrName = "deform"
kPluginNodeClassify = "utility/general"
kPluginNodeId = om2.MTypeId(0x001384c0)


def maya_useNewAPI():
    pass


class TensionMap(om2.MPxNode):

    def __init__(self):
        om2.MPxNode.__init__(self)
        self.isDeformedDirty = True
        self.isOrigDirty = True
        self.origEdgeLenArray = []
        self.deformedEdgeLenArray = []

    def initialize_ramp(self,
                        parentNode,
                        rampObj,
                        index,
                        position,
                        value,
                        interpolation):

        rampPlug = om2.MPlug(parentNode, rampObj)
        elementPlug = rampPlug.elementByLogicalIndex(index)

        positionPlug = elementPlug.child(0)
        positionPlug.setFloat(position)

        valuePlug = elementPlug.child(1)
        valuePlug.child(0).setFloat(value[0])
        valuePlug.child(1).setFloat(value[1])
        valuePlug.child(2).setFloat(value[2])

        interpPlug = elementPlug.child(2)
        interpPlug.setInt(interpolation)

    def postConstructor(self):
        values = [
            {"index": 0, "position": 0.0, "value": om2.MColor((0, 1, 0, 1))},
            {"index": 1, "position": 0.5, "value": om2.MColor((0, 0, 0, 1))},
            {"index": 2, "position": 1.0, "value": om2.MColor((1, 0, 0, 1))},
        ]
        for kwargs in values:
            self.initialize_ramp(parentNode=self.thisMObject(),
                                 rampObj=self.aColorRamp,
                                 interpolation=1,
                                 **kwargs)

    def setDependentsDirty(self, dirtyPlug, affectedPlugs):
        if dirtyPlug.partialName() == origAttrName:
            self.isOrigDirty = True
        if dirtyPlug.partialName() == deformedAttrName:
            self.isDeformedDirty = True

        if self.isOrigDirty or self.isDeformedDirty:
            outShapePlug = om2.MPlug(self.thisMObject(), self.aOutShape)
            affectedPlugs.append(outShapePlug)

    def compute(self, plug, data):

        if plug == self.aOutShape:

            thisObj = self.thisMObject()
            origHandle = data.inputValue(self.aOrigShape)
            deformedHandle = data.inputValue(self.aDeformedShape)
            outHandle = data.outputValue(self.aOutShape)
            colorRamp = om2.MRampAttribute(thisObj, self.aColorRamp)

            if self.isOrigDirty:
                self.isOrigDirty = False
                self.origEdgeLenArray = self.getEdgeLen(origHandle)

            if self.isDeformedDirty:
                self.isDeformedDirty = False
                self.deformedEdgeLenArray = self.getEdgeLen(deformedHandle)

            origEdges = self.origEdgeLenArray
            defmEdges = self.deformedEdgeLenArray

            if len(origEdges) == len(defmEdges):

                outHandle.copy(deformedHandle)
                outHandle.setMObject(deformedHandle.asMesh())

                outMesh = outHandle.asMesh()
                meshFn = om2.MFnMesh(outMesh)
                numVerts = meshFn.numVertices
                vertColors = om2.MColorArray()
                vertColors.setLength(numVerts)

                for i in range(numVerts):
                    delta = 0.5
                    delta += ((origEdges[i] - defmEdges[i]) / origEdges[i])

                    vertColor = colorRamp.getValueAtPosition(delta)
                    vertColors[i] = vertColor

                if not self.setAndAssignColors(meshFn, vertColors):
                    self.setVertexColors(meshFn, vertColors)

            else:
                print("Edge count doesn't match.")

        data.setClean(plug)

    def setVertexColors(self, meshFn, vertColors):
        """This cannot name a colorSet"""
        numVerts = meshFn.numVertices
        vertIds = om2.MIntArray()
        vertIds.setLength(numVerts)

        for i in range(numVerts):
            vertIds[i] = i

        meshFn.setVertexColors(vertColors, vertIds)

    def setAndAssignColors(self, meshFn, vertColors):
        """This requires colorSet to be pre-existed"""
        if "tensionCS" not in meshFn.getColorSetNames():
            # Sadly, this won't work :(
            # meshFn.createColorSet("tensionCS", False)
            # So we could not proceed.
            return False

        numFaceVerts = meshFn.numFaceVertices
        colorIdsOnFaceVertex = om2.MIntArray()
        colorIdsOnFaceVertex.setLength(numFaceVerts)

        for i in xrange(numFaceVerts):
            _, vertId = meshFn.getFaceAndVertexIndices(i, localVertex=False)
            colorIdsOnFaceVertex[i] = vertId

        meshFn.setColors(vertColors, "tensionCS")
        meshFn.assignColors(colorIdsOnFaceVertex, "tensionCS")
        return True

    def getEdgeLen(self, meshHandle):
        edgeLenArray = []
        meshObj = meshHandle.asMesh()
        edgeIter = om2.MItMeshEdge(meshObj)
        vertIter = om2.MItMeshVertex(meshObj)

        while not vertIter.isDone():
            connectedEdges = vertIter.getConnectedEdges()
            lengthSum = 0.0
            for i in range(len(connectedEdges)):
                edgeIter.setIndex(connectedEdges[i])
                length = edgeIter.length(om2.MSpace.kWorld)
                lengthSum += length * 1.0

            lenAvg = lengthSum / len(connectedEdges)
            edgeLenArray.append(lenAvg)
            vertIter.next()

        return edgeLenArray


def nodeCreator():
    return TensionMap()


def initialize():
    tAttr = om2.MFnTypedAttribute()

    TensionMap.aOrigShape = tAttr.create(origAttrName,
                                         origAttrName,
                                         om2.MFnMeshData.kMesh)
    tAttr.storable = True

    TensionMap.aDeformedShape = tAttr.create(deformedAttrName,
                                             deformedAttrName,
                                             om2.MFnMeshData.kMesh)
    tAttr.storable = True

    TensionMap.aOutShape = tAttr.create("out", "out", om2.MFnMeshData.kMesh)
    tAttr.writable = False
    tAttr.storable = False

    TensionMap.aColorRamp = om2.MRampAttribute().createColorRamp("color", "color")
    TensionMap.addAttribute(TensionMap.aOrigShape)
    TensionMap.addAttribute(TensionMap.aDeformedShape)
    TensionMap.addAttribute(TensionMap.aOutShape)
    TensionMap.addAttribute(TensionMap.aColorRamp)
    TensionMap.attributeAffects(TensionMap.aOrigShape, TensionMap.aOutShape)
    TensionMap.attributeAffects(TensionMap.aDeformedShape, TensionMap.aOutShape)
    TensionMap.attributeAffects(TensionMap.aColorRamp, TensionMap.aOutShape)


# AE template that put the main attributes into the main attribute section
# @staticmethod
def AEtemplateString(nodeName):
    templStr = ''
    templStr += 'global proc AE%sTemplate(string $nodeName)\n' % nodeName
    templStr += '{\n'
    templStr += 'editorTemplate -beginScrollLayout;\n'
    templStr += '   editorTemplate -beginLayout "Color Remaping" -collapse 0;\n'
    templStr += '       AEaddRampControl( $nodeName + ".color" );\n'
    templStr += '   editorTemplate -endLayout;\n'

    templStr += 'editorTemplate -addExtraControls; // add any other attributes\n'
    templStr += 'editorTemplate -endScrollLayout;\n'
    templStr += '}\n'

    return templStr


def initializePlugin(mobject):
    mplugin = om2.MFnPlugin(mobject)
    try:
        mplugin.registerNode(kPluginNodeName, kPluginNodeId,
                             nodeCreator, initialize)
        om.MGlobal.executeCommand(AEtemplateString(kPluginNodeName))
    except Exception:
        sys.stderr.write("Failed to register node: " + kPluginNodeName)
        raise


def uninitializePlugin(mobject):
    mplugin = om2.MFnPlugin(mobject)
    try:
        mplugin.deregisterNode(kPluginNodeId)
    except Exception:
        sys.stderr.write("Failed to deregister node: " + kPluginNodeName)
        raise
