import adsk.core, adsk.fusion, traceback, math

id = 'com-autodesk-fusion360-addins-teeth'
name = 'Gear'
description = 'Sketches a gear.'
resources = './resources'

radiusInit = 2.5
pitchInit = 0.5
pointInit = math.radians(45)

def run(context):
  try:
    global factories
    factories = []
    app = adsk.core.Application.get()
    ui = app.userInterface
    panel = ui.allToolbarPanels.itemById('SketchCreatePanel')
    menu = panel.controls.itemById(id + '-menu')
    if menu: return
    menu = panel.controls.addDropDown(name, resources, id + '-menu')
    external = External()
    factories.append(external)
    command = ui.commandDefinitions.itemById(id)
    if command: return
    command = ui.commandDefinitions.addButtonDefinition(id + '-external', 'External', description, resources)
    command.commandCreated.add(external)
    menu.controls.addCommand(command)
    internal = Internal()
    factories.append(internal)
    command = ui.commandDefinitions.addButtonDefinition(id + '-internal', 'Internal', description, resources)
    command.commandCreated.add(internal)
    menu.controls.addCommand(command)
    adsk.autoTerminate(False)
  except:
    if ui: ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class External(adsk.core.CommandCreatedEventHandler):
  def __init__(self):
    super().__init__()
  def notify(self, args):
    try:
      app = adsk.core.Application.get()
      ui = app.userInterface
      draw(False)
    except:
      if ui: ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class Internal(adsk.core.CommandCreatedEventHandler):
  def __init__(self):
    super().__init__()
  def notify(self, args):
    try:
      app = adsk.core.Application.get()
      ui = app.userInterface
      draw(True)
    except:
      if ui: ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def draw(internal: bool):
  sketch = adsk.fusion.Sketch.cast(adsk.core.Application.get().activeEditObject)
  if not sketch: return
  # Verbosity
  pt = adsk.core.Point3D.create
  ln = sketch.sketchCurves.sketchLines.addByTwoPoints
  cir = sketch.sketchCurves.sketchCircles.addByCenterRadius
  dim = sketch.sketchDimensions
  const = sketch.geometricConstraints
  aligned = adsk.fusion.DimensionOrientations.AlignedDimensionOrientation
  # Calculations
  radi = radiusInit
  circ = radi*2*math.pi
  point = pointInit
  count = math.floor(circ / pitchInit)
  pitch = math.radians(360 / count)
  slope = (point-pitch)/2 if internal else (point+pitch)/2
  depth = math.cos(slope)/math.sin(slope)*circ/count/2
  iface = radi + depth if internal else radi - depth
  # Pitch measure
  measure = ln(pt(-pitchInit/2, 0, 0), pt(pitchInit/2, 0, 0))
  measure.isConstruction = True
  dimPitch = dim.addDistanceDimension(measure.startSketchPoint, measure.endSketchPoint, aligned, pt(0, radi/8, 0)).parameter
  name = dimPitch.name
  dimPitch.name = name + 'Pitch'
  const.addHorizontal(measure)
  # The root circle
  edge = cir(pt(0, 0, 0), radi)
  edge.isConstruction = True
  dimEdge = dim.addDiameterDimension(edge, pt(radi/2, 0, 0)).parameter
  dimEdge.name = name + 'Edge'
  const.addMidPoint(edge.centerSketchPoint, measure)
  # The addendum circle
  base = cir(edge.centerSketchPoint.geometry, iface)
  base.isConstruction = True
  dimBase = dim.addDiameterDimension(base, pt(iface/-2, 0, 0), False).parameter
  dimBase.name = name + 'Base'
  const.addConcentric(edge, base)
  # The center line
  center = ln(pt(0, iface, 0), pt(0, radi, 0))
  center.isCenterLine = True
  const.addCoincident(center.startSketchPoint, base)
  const.addCoincident(center.endSketchPoint, edge)
  const.addCoincident(edge.centerSketchPoint, center)
  const.addVertical(center)
  # The azimuth line
  azi = ln(pt(math.sin(pitch)*iface, math.cos(pitch)*iface, 0), pt(math.sin(pitch)*radi, math.cos(pitch)*radi, 0))
  azi.isConstruction = True
  dimAzi = dim.addAngularDimension(center, azi, pt(math.sin(pitch/2)*(radi+depth), math.cos(pitch/2)*(radi+depth), 0)).parameter
  dimAzi.name = name + 'Azimuth'
  const.addCoincident(azi.startSketchPoint, base)
  const.addCoincident(azi.endSketchPoint, edge)
  const.addCoincident(edge.centerSketchPoint, azi)
  # The tooth
  left = ln(pt(math.sin(pitch*.5)*iface, math.cos(pitch*.5)*iface, 0), pt(math.sin(pitch*.5)*radi, math.cos(pitch*.5)*radi, 0))
  left.isConstruction = True
  const.addCoincident(left.startSketchPoint, base)
  const.addCoincident(left.endSketchPoint, edge)
  const.addCoincident(edge.centerSketchPoint, left)
  right = ln(pt(math.sin(pitch*1.5)*iface, math.cos(pitch*1.5)*iface, 0), pt(math.sin(pitch*1.5)*radi, math.cos(pitch*1.5)*radi, 0))
  right.isConstruction = True
  const.addCoincident(right.startSketchPoint, base)
  const.addCoincident(right.endSketchPoint, edge)
  const.addCoincident(edge.centerSketchPoint, right)
  dimSpan = dim.addAngularDimension(left, right, pt(math.sin(pitch)*radi/2, math.cos(pitch)*radi/2, 0)).parameter
  dimSpan.name = name + 'PitchAngle'
  midl = ln(left.startSketchPoint, azi.endSketchPoint)
  midr = ln(right.startSketchPoint, azi.endSketchPoint)
  const.addEqual(midl, midr)
  dimPoint = dim.addAngularDimension(midl, midr, pt(math.sin(pitch)*radi/4, math.cos(pitch)*radi/4, 0)).parameter
  dimPoint.name = name + 'Point'
  dimPoint.value = point
  # The pattern
  input = const.createCircularPatternInput([midl, midr], edge.centerSketchPoint)
  input.quantity = adsk.core.ValueInput.createByString('floor((' + dimEdge.name + '/1' + dimEdge.unit + ')*PI/(' + dimPitch.name + '/1' + dimPitch.unit + '))')
  input.totalAngle = adsk.core.ValueInput.createByString('360 deg')
  pattern = const.addCircularPattern(input)
  pattern.quantity.name = name + 'Count'
  dimSpan.expression = '360 deg /' + pattern.quantity.name
  dimAzi.expression = dimSpan.name

