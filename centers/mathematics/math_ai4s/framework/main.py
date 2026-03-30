#!/usr/bin/env python3
"""
MathAI4S Framework — Main Entry Point
数学AI4S框架 —— 主入口

Usage:
  python3 -m framework.main explore --from 65 --to 359
  python3 -m framework.main verify --result result.json
  python3 -m framework.main maintenance [--dry-run]
  python3 -m framework.main status

Author: Δ (Delta-Forge)
Date: 2026-03-30
"""

import argparse
import sys
import json
from pathlib import Path
from datetime import datetime

# 确保框架模块可导入
sys.path.insert(0, str(Path(__file__).parent))

try:
    # Try relative imports first (when run as module)
    from .core_architecture import ResearchSession, ImplicationResult, ProofStatus
    from .exploration_strategies import StrategyOrchestrator
    from .verification_layer import VerificationPipeline
    from .self_maintenance import SelfMaintenance
except ImportError:
    # Fall back to absolute imports (when run directly)
    from core_architecture import ResearchSession, ImplicationResult, ProofStatus
    from exploration_strategies import StrategyOrchestrator
    from verification_layer import VerificationPipeline
    from self_maintenance import SelfMaintenance


def cmd_explore(args):
    """探索命令"""
    print("=" * 70)
    print("MathAI4S Research Framework — Exploration Mode")
    print("=" * 70)
    
    # 创建研究会话
    session = ResearchSession(
        session_id=f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        target_implications=[(args.from_eq, args.to_eq)]
    )
    
    print(f"\nTarget: Equation{args.from_eq} => Equation{args.to_eq}")
    print(f"Max Effort: {args.max_effort}")
    print("\nExploring...")
    
    # 执行探索
    orchestrator = StrategyOrchestrator()
    result = orchestrator.explore(args.from_eq, args.to_eq, args.max_effort)
    
    session.add_result(result)
    session.end_time = datetime.now().isoformat()
    session.status = "completed"
    
    # 输出结果
    print("\n" + "=" * 70)
    print("RESULT")
    print("=" * 70)
    print(f"Status: {result.status.name}")
    print(f"Verification Level: {result.verification_level.name}")
    print(f"Tool Used: {result.tool_used}")
    
    if result.counterexample:
        print(f"\nCounterexample Found:")
        print(f"  Magma Order: {result.counterexample.order}")
        print(f"  Cayley Table:")
        table = result.counterexample.to_cayley_table()
        for row in table:
            print(f"    {row}")
    
    if result.proof_data:
        print(f"\nProof Data:")
        for key, value in result.proof_data.items():
            print(f"  {key}: {value}")
    
    # 保存结果
    if args.output:
        output_path = Path(args.output)
        with open(output_path, 'w') as f:
            json.dump(session.to_report(), f, indent=2)
        print(f"\nSession saved to: {output_path}")
    
    # 生成Lean代码
    print("\n" + "=" * 70)
    print("LEAN CODE (Template)")
    print("=" * 70)
    print(result.to_lean_theorem())
    
    return 0


def cmd_verify(args):
    """验证命令"""
    print("=" * 70)
    print("MathAI4S Research Framework — Verification Mode")
    print("=" * 70)
    
    # 加载结果
    result_path = Path(args.result)
    if not result_path.exists():
        print(f"Error: Result file not found: {result_path}")
        return 1
    
    with open(result_path) as f:
        data = json.load(f)
    
    # 这里简化处理，实际需要完整解析
    print(f"\nLoaded result from: {result_path}")
    print(f"Verification not fully implemented in this demo")
    
    return 0


def cmd_maintenance(args):
    """维护命令"""
    print("=" * 70)
    print("MathAI4S Research Framework — Maintenance Mode")
    print("=" * 70)
    
    maint = SelfMaintenance()
    
    if args.status:
        # 快速状态检查
        health = maint.health_check()
        print(f"\nHealth Status: {health['status']}")
        print(f"Timestamp: {health['timestamp']}")
        print(f"Backups Available: {health['backups_available']}")
        print(f"\nIntegrity Checks:")
        for check, passed in health['integrity'].items():
            status = "✓" if passed else "✗"
            print(f"  [{status}] {check}")
        return 0
    
    # 执行维护
    print(f"\nRunning maintenance (dry_run={args.dry_run})...")
    report = maint.run_maintenance(dry_run=args.dry_run)
    
    print(f"\nActions Taken:")
    for action in report.actions_taken:
        print(f"  • {action}")
    
    print(f"\nSpace Reclaimed: {report.space_reclaimed:,} bytes")
    
    if report.warnings:
        print(f"\nWarnings:")
        for warning in report.warnings:
            print(f"  ! {warning}")
    
    return 0


def main():
    """主入口"""
    parser = argparse.ArgumentParser(
        description="MathAI4S Research Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Explore an implication
  python3 -m framework.main explore --from 65 --to 359

  # Run with higher effort limit
  python3 -m framework.main explore --from 65 --to 359 --max-effort 100000

  # Check system health
  python3 -m framework.main maintenance --status

  # Clean up old files (dry run)
  python3 -m framework.main maintenance --dry-run

  # Actually clean up
  python3 -m framework.main maintenance
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # explore command
    explore_parser = subparsers.add_parser('explore', help='Explore an implication')
    explore_parser.add_argument('--from', type=int, required=True, dest='from_eq',
                               help='Source equation ID')
    explore_parser.add_argument('--to', type=int, required=True, dest='to_eq',
                               help='Target equation ID')
    explore_parser.add_argument('--max-effort', type=int, default=50000,
                               help='Maximum computational effort')
    explore_parser.add_argument('-o', '--output', type=str,
                               help='Output file for session report')
    
    # verify command
    verify_parser = subparsers.add_parser('verify', help='Verify a result')
    verify_parser.add_argument('result', help='Result file to verify')
    
    # maintenance command
    maint_parser = subparsers.add_parser('maintenance', help='System maintenance')
    maint_parser.add_argument('--dry-run', action='store_true',
                             help='Show what would be done without doing it')
    maint_parser.add_argument('--status', action='store_true',
                             help='Quick health check')
    
    args = parser.parse_args()
    
    if args.command == 'explore':
        return cmd_explore(args)
    elif args.command == 'verify':
        return cmd_verify(args)
    elif args.command == 'maintenance':
        return cmd_maintenance(args)
    else:
        parser.print_help()
        return 0


if __name__ == '__main__':
    sys.exit(main())
