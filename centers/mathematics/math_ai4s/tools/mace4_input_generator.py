#!/usr/bin/env python3
"""
Mace4 Input Generator for ETP Open Implications
Generates Mace4 input files to search for counterexamples to ETP implications.

Usage:
  python3 mace4_input_generator.py <eq_from> <eq_to> <eq_from_def> <eq_to_def>
Example:
  python3 mace4_input_generator.py 65 359 "x = y ◇ (x ◇ (y ◇ x))" "x ◇ x = (x ◇ x) ◇ x"
"""

import sys
import os

def leanto_mace4(lean_eq):
    """Convert Lean equation notation to Mace4 notation."""
    # Replace Lean notation with Mace4 notation
    mace4_eq = lean_eq
    mace4_eq = mace4_eq.replace('◇', '*')
    mace4_eq = mace4_eq.replace('×', '*')
    mace4_eq = mace4_eq.replace('·', '*')
    # Handle subscripts - strip them for Mace4
    mace4_eq = mace4_eq.replace('_', '')
    return mace4_eq

def generate_mace4_input(eq_from_num, eq_to_num, eq_from_def, eq_to_def, max_domain=4):
    """Generate a Mace4 input file to search for a counterexample."""
    
    eq_from_m4 = leanto_mace4(eq_from_def)
    eq_to_m4 = leanto_mace4(eq_to_def)
    
    # The negation of implication: A => B means A implies B
    # Counterexample: A holds but B does not
    # So we want to find a model satisfying eq_from AND NOT eq_to
    
    input_text = f"""% ETP Implication Search
% Seeking counterexample to: Equation{eq_from_num} => Equation{eq_to_num}
%
% Source definition (Lean notation):
%   Eq{eq_from_num}: {eq_from_def}
%   Eq{eq_to_num}: {eq_to_def}
%
% Mace4 notation: * denotes the binary operation

set(prolog).
formulas(assumptions).
% Equation {eq_from_num}: {eq_from_m4}
{canonize_assumptions(eq_from_m4)}.

% Negation of Equation {eq_to_num}: NOT ({eq_to_m4})
% A counterexample satisfies eq_from but violates eq_to
{canonize_negation(eq_to_m4)}.
end_of_list.

formulas(go).
end_of_list.
"""
    return input_text

def canonize_assumptions(eq):
    """Convert equation to canonical Horn form for Mace4."""
    # Most equational laws are universally quantified
    # Mace4 accepts them directly as assumptions
    return f"  (all x all y all z all w {eq})"

def canonize_negation(eq):
    """Negate an equation for Mace4."""
    # Negation of (t1 = t2) is (t1 /= t2)
    negated = eq.replace('=', '/=')
    return f"  (exists x {negated.replace('x *', 'x *').replace('* x', '* x')})"

def generate_both_directions(eq_from_num, eq_to_num, eq_from_def, eq_to_def):
    """Generate inputs for both directions of the implication."""
    
    input_forward = generate_mace4_input(
        eq_from_num, eq_to_num, eq_from_def, eq_to_def
    )
    
    # For reverse: find model satisfying eq_to but NOT eq_from
    input_reverse = generate_mace4_input(
        eq_to_num, eq_from_num, eq_to_def, eq_from_def
    )
    
    return input_forward, input_reverse

if __name__ == "__main__":
    if len(sys.argv) >= 5:
        eq_from = sys.argv[1]
        eq_to = sys.argv[2]
        eq_from_def = sys.argv[3]
        eq_to_def = sys.argv[4]
        
        inp_forward, inp_reverse = generate_both_directions(
            eq_from, eq_to, eq_from_def, eq_to_def
        )
        
        basename = f"eq{eq_from}_to_eq{eq_to}"
        
        with open(f"search_{basename}_forward.inp", "w") as f:
            f.write(inp_forward)
        print(f"Written: search_{basename}_forward.inp")
        
        with open(f"search_{basename}_reverse.inp", "w") as f:
            f.write(inp_reverse)
        print(f"Written: search_{basename}_reverse.inp")
    else:
        # Default: generate for the first task (Eq65 => Eq359)
        eq_from_num, eq_to_num = "65", "359"
        eq_from_def = "x = y ◇ (x ◇ (y ◇ x))"
        eq_to_def = "x ◇ x = (x ◇ x) ◇ x"
        
        inp_forward, inp_reverse = generate_both_directions(
            eq_from_num, eq_to_num, eq_from_def, eq_to_def
        )
        
        for suffix, content in [
            ("forward", inp_forward),
            ("reverse", inp_reverse),
        ]:
            fname = f"search_eq65_eq359_{suffix}.inp"
            with open(fname, "w") as f:
                f.write(content)
            print(f"Written: {fname}")
