#!/usr/bin/env python3
"""
Script to test the newly trained T5 clinical model
"""

import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from models.quick_model_test import QuickClinicalT5Tester

def main():
    print("🚀 Starting T5 Clinical Model Evaluation")
    print("=" * 60)
    
    # Initialize tester
    tester = QuickClinicalT5Tester()
    
    # Load model
    print("\n📥 Loading model...")
    if not tester.load_model():
        print("❌ Failed to load model. Exiting.")
        return
    
    print("\n🧪 Running sample tests...")
    sample_results = tester.quick_sample_test()
    
    print("\n📊 Running test set evaluation...")
    test_results = tester.sample_test_set_evaluation(sample_size=50)
    
    print("\n📝 Generating report...")
    report = tester.generate_quick_report(sample_results, test_results)
    
    # Save report
    report_path = "d:/projects/healthca/model_evaluation_report.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n✅ Evaluation complete! Report saved to: {report_path}")
    print("\n" + "=" * 60)
    print(report)

if __name__ == "__main__":
    main()