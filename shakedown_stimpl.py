from stimpl.expression import *
from stimpl.runtime import *

if __name__=='__main__':
  program = Print(Eq(IntLiteral(7),IntLiteral(7)))
  run_stimpl(program)
