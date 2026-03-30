#!/usr/bin/env python3
"""
Pure Python Magma Search — No external dependencies required.
Searches for small magmas satisfying/dissatisfying given equational laws.

This replaces Mace4 for the first sub-task when Mace4 is not available.
"""

import itertools
from typing import Callable, List, Dict, Tuple

# Equation types: functions that take a magma table and return True if satisfied
# Magma table: dict of (x,y) -> z, where x,y,z are integers 0..n-1

def parse_equation(lean_eq: str) -> str:
    """Convert Lean notation to Python expression."""
    expr = lean_eq
    expr = expr.replace('◇', '*')
    expr = expr.replace('×', '*')
    expr = expr.replace('·', '*')
    expr = expr.strip().strip('.-')
    return expr

def evaluate_expression(expr: str, bindings: Dict[str, int]) -> int:
    """Evaluate an expression given variable bindings."""
    # Very simple evaluator for flat expressions
    # Handles: x, y, x*x, x*y, (x*y)*z, etc.
    expr = expr.strip()
    
    # Remove outer parentheses if present
    while expr.startswith('(') and expr.endswith(')'):
        expr = expr[1:-1]
    
    # Handle x*y type expressions
    def replace_ops(m):
        return f')*({m.group(1)}'
    
    # Convert to a computable form
    # We'll use eval with __import__ trick - but let's be safer and do it manually
    
    # Simple recursive descent would be better, but for now let's do string replacement
    # This handles flat expressions like "x * y", "x * x", "(x * y) * z"
    
    # Replace all identifiers with their values
    for var, val in bindings.items():
        expr = expr.replace(var, str(val))
    
    # Now replace * with multiplication
    expr = expr.replace('*', '*')  # no-op in Python
    
    # Handle the expression - try to eval safely
    allowed_chars = '0123456789()*+-= '
    if all(c in allowed_chars for c in expr):
        return eval(expr)
    else:
        raise ValueError(f"Unsafe expression: {expr}")

def satisfies_eq65(table, n):
    """Check if magma satisfies Equation 65: x = y ◇ (x ◇ (y ◇ x))"""
    for x in range(n):
        for y in range(n):
            # t1 = y * (x * (y * x))
            inner1 = table[(y, table[(x, table[(y, x)])])]
            if x != inner1:
                return False
    return True

def violates_eq359(table, n):
    """Check if magma violates Equation 359: x ◇ x = (x ◇ x) ◇ x
    Returns True if VIOLATES (i.e., the implication counterexample exists).
    """
    for x in range(n):
        xx = table[(x, x)]
        xxx = table[(xx, x)]
        if xx != xxx:
            return True  # Violates - counterexample found!
    return False  # Satisfies Eq359

def satisfies_eq359(table, n):
    """Check if magma satisfies Equation 359: x ◇ x = (x ◇ x) ◇ x"""
    for x in range(n):
        xx = table[(x, x)]
        xxx = table[(xx, x)]
        if xx != xxx:
            return False
    return True

def generate_all_magmas(n: int) -> int:
    """Generate all magmas on n elements and test Eq65 => Eq359."""
    count = 0
    counterexamples = []
    
    # A magma is a multiplication table: n^2 entries, each in {0..n-1}
    # Total possibilities: n^(n^2)
    num_magmas = n ** (n * n)
    print(f"Searching all {num_magmas} magmas on {n} elements...")
    
    # Use a more efficient enumeration
    # Each entry is (i,j) -> k where k in range(n)
    entries = list(range(n)) * (n * n)
    
    count = 0
    found = 0
    
    # For n=2: 2^(4) = 16 magmas
    # For n=3: 3^(9) = 19683 magmas
    # For n=4: 4^(16) = 4,294,967,296 magmas (too many!)
    
    if n <= 3:
        # Full enumeration
        for combo in itertools.product(range(n), repeat=n*n):
            table = {}
            idx = 0
            for i in range(n):
                for j in range(n):
                    table[(i, j)] = combo[idx]
                    idx += 1
            
            count += 1
            if satisfies_eq65(table, n) and violates_eq359(table, n):
                found += 1
                counterexamples.append((n, dict(table)))
                print(f"  FOUND counterexample #{found}! n={n}")
                print(f"  Multiplication table: {dict(table)}")
    
    return count, counterexamples

def test_specific_magma(table, n):
    """Test a specific magma and explain the result."""
    print(f"\nMagma on {n} elements:")
    print("Multiplication table:")
    for i in range(n):
        row = [table[(i, j)] for j in range(n)]
        print(f"  {row}")
    
    eq65 = satisfies_eq65(table, n)
    eq359 = satisfies_eq359(table, n)
    violates359 = violates_eq359(table, n)
    
    print(f"  Satisfies Eq65: {eq65}")
    print(f"  Satisfies Eq359: {eq359}")
    print(f"  Violates Eq359: {violates359}")
    
    if eq65 and violates359:
        print("  *** COUNTEREXAMPLE: Eq65 holds but Eq359 does NOT hold! ***")
        print("  This means: Equation65 does NOT imply Equation359")
    elif eq65 and eq359:
        print("  Both hold: Eq65 implies Eq359 (so far, no counterexample)")
    else:
        print("  Eq65 not satisfied")
    
    return eq65, violates359

def main():
    print("=" * 60)
    print("ETP Sub-task: Equation65 => Equation359")
    print("Question: Does every magma satisfying x=y*(x*(y*x)) also satisfy x*x=(x*x)*x?")
    print("=" * 60)
    
    # Step 1: Test specific small magmas
    print("\n--- Phase 1: Specific magma tests ---")
    
    # Test n=2: there are only 2^4 = 16 magmas
    print("\nAll magmas on 2 elements (16 total):")
    count2, ce2 = generate_all_magmas(2)
    print(f"Total: {count2}, Counterexamples: {len(ce2)}")
    
    if ce2:
        for n, table in ce2:
            test_specific_magma(table, n)
    
    # Test n=3: 3^9 = 19683 - takes a few seconds
    print(f"\nAll magmas on 3 elements ({3**9} total):")
    count3, ce3 = generate_all_magmas(3)
    print(f"Total: {count3}, Counterexamples: {len(ce3)}")
    
    if ce3:
        for n, table in ce3:
            test_specific_magma(table, n)
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    total_ce = len(ce2) + len(ce3)
    if total_ce > 0:
        print(f"FOUND {total_ce} COUNTEREXAMPLE(S)!")
        print("Equation65 does NOT imply Equation359")
        print("Result: The implication is FALSE")
    else:
        print("No counterexample found in n=2,3.")
        print("The implication MAY be true (requires proof)")
        print("For n=4: 4^16 = 4 billion - too many to search exhaustively")

if __name__ == "__main__":
    main()

def sample_magmas(n, num_samples=10000):
    """Sample random magmas to search for counterexamples in n=4+."""
    import random
    print(f"\n--- Phase 2: Random sampling for n={n} ---")
    print(f"Sampling {num_samples} random magmas...")
    
    counterexamples = []
    for i in range(num_samples):
        table = {}
        for i2 in range(n):
            for j2 in range(n):
                table[(i2, j2)] = random.randint(0, n-1)
        
        if satisfies_eq65(table, n) and violates_eq359(table, n):
            counterexamples.append(dict(table))
            print(f"  FOUND counterexample #{len(counterexamples)}! n={n}")
    
    return counterexamples

if __name__ == "__main__":
    import random
    # Run random sampling for n=4
    random.seed(42)
    ce4 = sample_magmas(4, 100000)
    print(f"\nRandom sampling n=4: found {len(ce4)} counterexamples out of 100000")
    if ce4:
        for table in ce4:
            test_specific_magma(table, 4)
