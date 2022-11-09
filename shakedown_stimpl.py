from stimpl.expression import *
from stimpl.runtime import *

if __name__=='__main__':
  program = (Divide(FloatingPointLiteral(6.0),FloatingPointLiteral(3.0)))
  run_stimpl(program)
