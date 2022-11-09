from stimpl.expression import *
from stimpl.runtime import *

if __name__=='__main__':
  program = Print(Divide(IntLiteral(6),IntLiteral(4)))
  run_stimpl(program)
