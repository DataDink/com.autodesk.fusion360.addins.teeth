import adsk.core, adsk.fusion, traceback, math

id = 'com-autodesk-fusion360-addins-teeth'
name = 'Gear'
description = 'Sketches a gear.'

defaultRadius = 2.5
defaultSpacing = 0.5
defaultOrientation = math.radians(45)

def run(context):
  try:
    global factories
    factories = []
    app = adsk.core.Application.get()
    ui = app.userInterface
    panel = ui.allToolbarPanels.itemById('SketchCreatePanel')
    outward = Outward()
    factories.append(outward)
    command = ui.commandDefinitions.itemById(id) 
    if not command: command = ui.commandDefinitions.addButtonDefinition(id, name, description, './resources')
    command.commandCreated.add(outward)
    panel.controls.addCommand(command)
    inward = Inward()
    factories.append(inward)
    invertedId = id + '-inverted'
    command = ui.commandDefinitions.itemById(invertedId)
    if not command: command = ui.commandDefinitions.addButtonDefinition(invertedId, name + ' (Inverted)', description, './resources')
    command.commandCreated.add(inward)
    panel.controls.addCommand(command)
    adsk.autoTerminate(False)
  except:
    if ui: ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class Outward(adsk.core.CommandCreatedEventHandler):
  def __init__(self):
    super().__init__()
  def notify(self, args):
    try:
      app = adsk.core.Application.get()
      ui = app.userInterface
      draw(False)
    except:
      self.transaction.abort()
      if ui: ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class Inward(adsk.core.CommandCreatedEventHandler):
  def __init__(self):
    super().__init__()
  def notify(self, args):
    try:
      app = adsk.core.Application.get()
      ui = app.userInterface
      draw(True)
    except:
      self.transaction.abort()
      if ui: ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def draw(invert: bool):
  sketch = adsk.fusion.Sketch.cast(adsk.core.Application.get().activeEditObject)
  if not sketch: return
  deg = math.radians(1)
  radius = defaultRadius
  spacing = defaultSpacing
  orientation = defaultOrientation
  center = sketch.sketchCurves.sketchLines.addByTwoPoints(adsk.core.Point3D.create(0, 0, 0), adsk.core.Point3D.create(0, radius, 0))
  center.isCenterLine = True
  sketch.geometricConstraints.addVertical(center)
  dimRadius = sketch.sketchDimensions.addDistanceDimension(center.startSketchPoint, center.endSketchPoint, adsk.fusion.DimensionOrientations.AlignedDimensionOrientation, adsk.core.Point3D.create(0, radius / 2, 0)).parameter
  edge = sketch.sketchCurves.sketchCircles.addByCenterRadius(center.startSketchPoint.geometry, radius)
  edge.isConstruction = True
  sketch.geometricConstraints.addCoincident(center.startSketchPoint, edge.centerSketchPoint)
  sketch.geometricConstraints.addCoincident(center.endSketchPoint, edge)
  extent = center.endSketchPoint if orientation == 0 else adsk.core.Point3D.create(math.sin(orientation)*radius, math.cos(orientation)*radius, 0)
  orient = center if orientation == 0 else sketch.sketchCurves.sketchLines.addByTwoPoints(center.startSketchPoint, extent)
  orient.isConstruction = True
  if orientation != 0:
    sketch.geometricConstraints.addCoincident(orient.endSketchPoint, edge)
    sketch.sketchDimensions.addAngularDimension(center, orient, adsk.core.Point3D.create(math.sin(orientation/2)*radius, math.cos(orientation/2)*radius, 0))
  measure = sketch.sketchCurves.sketchLines.addByTwoPoints(adsk.core.Point3D.create(0,0,0), adsk.core.Point3D.create(spacing,0,0))
  measure.isConstruction = True
  dimSpacing = sketch.sketchDimensions.addDistanceDimension(measure.startSketchPoint, measure.endSketchPoint, adsk.fusion.DimensionOrientations.AlignedDimensionOrientation, adsk.core.Point3D.create(spacing/2, 0, 0)).parameter
  sketch.geometricConstraints.addMidPoint(orient.endSketchPoint, measure)
  sketch.geometricConstraints.addPerpendicular(orient, measure)
  countFormula = 'floor((' + dimRadius.name + '/1' + dimRadius.unit + ') * 2 * PI / (' + dimSpacing.name + '/1' + dimSpacing.unit + '))'
  guideFormula = '360 deg/' + countFormula + '/2'
  project = radius * 1.5 if invert else radius * 0.5
  left = sketch.sketchCurves.sketchLines.addByTwoPoints(orient.endSketchPoint, adsk.core.Point3D.create(math.sin(orientation-deg*2)*project, math.cos(orientation-deg*2)*project, 0))
  dimLeft = sketch.sketchDimensions.addAngularDimension(orient, left, adsk.core.Point3D.create(math.sin(orientation-deg)*project, math.cos(orientation-deg)*project, 0))
  dimLeft.value = math.radians(45/2)
  dimLeft.textPosition = center.startSketchPoint.geometry
  guideLeft = sketch.sketchCurves.sketchLines.addByTwoPoints(center.startSketchPoint, left.endSketchPoint)
  guideLeft.isConstruction = True
  dimGuideLeft = sketch.sketchDimensions.addAngularDimension(orient, guideLeft, adsk.core.Point3D.create(math.sin(orientation-deg)*project, math.cos(orientation-deg)*project, 0))
  dimGuideLeft.parameter.expression = guideFormula
  dimGuideLeft.textPosition = center.startSketchPoint.geometry
  right = sketch.sketchCurves.sketchLines.addByTwoPoints(orient.endSketchPoint, adsk.core.Point3D.create(math.sin(orientation+deg*2)*project, math.cos(orientation+deg*2)*project, 0))
  dimRight = sketch.sketchDimensions.addAngularDimension(orient, right, adsk.core.Point3D.create(math.sin(orientation+deg)*project, math.cos(orientation+deg)*project, 0))
  dimRight.value = math.radians(45/2)
  dimRight.textPosition = center.startSketchPoint.geometry
  guideRight = sketch.sketchCurves.sketchLines.addByTwoPoints(center.startSketchPoint, right.endSketchPoint)
  guideRight.isConstruction = True
  dimGuideRight = sketch.sketchDimensions.addAngularDimension(orient, guideRight, adsk.core.Point3D.create(math.sin(orientation+deg)*project, math.cos(orientation+deg)*project, 0))
  dimGuideRight.parameter.expression = guideFormula
  dimGuideRight.textPosition = center.startSketchPoint.geometry
  pattern = sketch.geometricConstraints.createCircularPatternInput([left, right], center.startSketchPoint)
  pattern.quantity = adsk.core.ValueInput.createByString(countFormula)
  pattern.totalAngle = adsk.core.ValueInput.createByString('360 deg')
  sketch.geometricConstraints.addCircularPattern(pattern)
