"""
  The TapSpeak demo shows Cozmo responding to cube tap events. A
  TapTrans transition is used to set up a handler for taps. The
  example also illustrates how the TapTrans transition does wildcard
  matching if not given an argument. By passing a cube as an argument
  to the TapTrans constructor can use it to look for taps on a
  specific cube.

  Behavior: Cozmo starts out by saying 'Tap a cube'. Then, every time
  a cube is tapped, Cozmo says the cube name and goes back to
  listening for more tap events.
"""

from cozmo_fsm import *

from cozmo_fsm import *

class SayCube(Say):
    """Say the name of a cube."""
    def start(self, event=None, \
              cube_names = ['paperclip', 'anglepoise lamp', 'deli slicer']):
        cube_number = next(k for k,v in self.robot.world.light_cubes.items() \
                               if v == event.source)
        self.text = cube_names[cube_number-1]
        super().start(event)

class TapSpeak(StateMachineProgram):
    def setup(self):
        """
            intro: Say('Tap a cube.') =C=> wait
    
            wait: StateNode() =Tap()=> speak
    
            speak: SayCube() =C=> wait
        """
        
        # Code generated by genfsm on Mon Feb 17 03:16:53 2020:
        
        intro = Say('Tap a cube.') .set_name("intro") .set_parent(self)
        wait = StateNode() .set_name("wait") .set_parent(self)
        speak = SayCube() .set_name("speak") .set_parent(self)
        
        completiontrans1 = CompletionTrans() .set_name("completiontrans1")
        completiontrans1 .add_sources(intro) .add_destinations(wait)
        
        taptrans1 = TapTrans() .set_name("taptrans1")
        taptrans1 .add_sources(wait) .add_destinations(speak)
        
        completiontrans2 = CompletionTrans() .set_name("completiontrans2")
        completiontrans2 .add_sources(speak) .add_destinations(wait)
        
        return self
