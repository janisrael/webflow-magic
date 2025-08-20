#!/usr/bin/env python3
"""
SEO Service Test Script
Tests the SEO optimization functionality with sample HTML content
"""

import os
import sys
import json
from datetime import datetime

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from services.seo_service import SEOService
    print("✅ SEO Service imported successfully")
except ImportError as e:
    print(f"❌ Failed to import SEO Service: {e}")
    print("Make sure you have created the services/seo_service.py file")
    sys.exit(1)


def test_basic_seo_optimization():
    """Test basic SEO optimization without API keys"""
    print("\n🧪 Testing Basic SEO Optimization (No API Keys)")
    print("-" * 50)
    
    # Sample HTML content
    sample_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>About Our Restaurant</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body>
        <h1>Welcome to Our Restaurant</h1>
        <h2>Our Story</h2>
        <p>We are a family-owned restaurant serving delicious Italian cuisine for over 20 years. Our chefs use only the freshest ingredients to create authentic dishes that will transport you to Italy.</p>
        <img src="restaurant-interior.jpg" alt="">
        <h2>Our Menu</h2>
        <p>From traditional pasta dishes to wood-fired pizzas, our menu offers something for everyone. We also have an extensive wine list featuring Italian and local wines.</p>
        <img src="pasta-dish.jpg" alt="">
    </body>
    </html>
    """
    
    # Initialize SEO service without API keys
    seo_service = SEOService()
    
    try:
        # Run optimization
        result = seo_service.analyze_and_optimize_page(
            html_content=sample_html,
            page_title="About Our Restaurant",
            business_type="restaurant",
            target_location="New York, NY"
        )
        
        print(f"✅ SEO optimization completed successfully!")
        print(f"📊 SEO Score: {result['seo_score']['score']}/100 ({result['seo_score']['status']})")
        print(f"🎯 Focus Keywords: {', '.join(result['seo_data']['focus_keywords'][:3])}")
        print(f"📈 Trending Keywords Found: {len(result['trending_keywords'])}")
        print(f"💡 Recommendations: {len(result['recommendations'])}")
        
        # Show some key optimizations
        print(f"\n🔧 Key Optimizations Applied:")
        print(f"   • Meta Title: {result['seo_data']['meta_title'][:60]}...")
        print(f"   • Meta Description: {result['seo_data']['meta_description'][:80]}...")
        print(f"   • Schema Type: {result['seo_data']['schema_type']}")
        
        # Show SEO score breakdown
        print(f"\n📊 SEO Score Breakdown:")
        for category, details in result['seo_score']['details'].items():
            status_emoji = "✅" if details['score'] >= 8 else "⚠️" if details['score'] >= 5 else "❌"
            print(f"   {status_emoji} {category.title()}: {details['score']}/10 - {details['status']}")
        
        return True
        
    except Exception as e:
        print(f"❌ SEO optimization failed: {e}")
        return False


def test_with_api_keys():
    """Test SEO optimization with API keys if available"""
    print("\n🔑 Testing SEO Optimization with API Keys")
    print("-" * 50)
    
    openai_key = os.getenv('OPENAI_API_KEY')
    serp_key = os.getenv('SERP_API_KEY')
    
    if not openai_key and not serp_key:
        print("ℹ️ No API keys found in environment variables.")
        print("   Set OPENAI_API_KEY and/or SERP_API_KEY to test advanced features.")
        return True
    
    print(f"🔑 OpenAI Key: {'✅ Found' if openai_key else '❌ Missing'}")
    print(f"🔑 SerpAPI Key: {'✅ Found' if serp_key else '❌ Missing'}")
    
    # Sample HTML for tech company
    tech_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Software Solutions</title>
    </head>
    <body>
        <h1>Revolutionary AI Software Solutions</h1>
        <p>We develop cutting-edge artificial intelligence software that transforms businesses. Our machine learning algorithms help companies automate processes and gain insights from their data.</p>
        <h2>Our Services</h2>
        <p>From natural language processing to computer vision, we offer comprehensive AI solutions tailored to your needs.</p>
    </body>
    </html>
    """
    
    try:
        # Initialize with API keys
        seo_service = SEOService(openai_key, serp_key)
        
        result = seo_service.analyze_and_optimize_page(
            html_content=tech_html,
            page_title="AI Software Solutions",
            business_type="technology",
            target_location="San Francisco, CA"
        )
        
        print(f"✅ Advanced SEO optimization completed!")
        print(f"📊 SEO Score: {result['seo_score']['score']}/100")
        print(f"🤖 AI-Generated Meta Title: {result['seo_data']['meta_title']}")
        print(f"🎯 Trending Keywords: {', '.join(result['trending_keywords'][:5])}")
        
        return True
        
    except Exception as e:
        print(f"⚠️ Advanced optimization failed: {e}")
        print("   This might be due to API rate limits or invalid keys.")
        return False


def test_multiple_business_types():
    """Test SEO optimization for different business types"""
    print("\n🏢 Testing Multiple Business Types")
    print("-" * 50)
    
    business_tests = [
        {
            "type": "health",
            "location": "Chicago, IL",
            "html": "<html><head><title>Medical Clinic</title></head><body><h1>Professional Medical Care</h1><p>Comprehensive healthcare services for families.</p></body></html>"
        },
        {
            "type": "education",
            "location": "Boston, MA",
            "html": "<html><head><title>Online Learning Platform</title></head><body><h1>Learn New Skills Online</h1><p>Professional courses and certifications.</p></body></html>"
        },
        {
            "type": "retail",
            "location": "Austin, TX",
            "html": "<html><head><title>Fashion Store</title></head><body><h1>Latest Fashion Trends</h1><p>Discover the newest styles and accessories.</p></body></html>"
        }
    ]
    
    seo_service = SEOService()
    success_count = 0
    
    for test in business_tests:
        try:
            result = seo_service.analyze_and_optimize_page(
                html_content=test["html"],
                page_title=f"{test['type'].title()} Business",
                business_type=test["type"],
                target_location=test["location"]
            )
            
            print(f"✅ {test['type'].title()} Business: {result['seo_score']['score']}/100")
            success_count += 1
            
        except Exception as e:
            print(f"❌ {test['type'].title()} Business: Failed ({e})")
    
    print(f"\n📊 Business Type Tests: {success_count}/{len(business_tests)} successful")
    return success_count == len(business_tests)


def save_test_results():
    """Save a sample SEO report for inspection"""
    print("\n💾 Generating Sample SEO Report")
    print("-" * 50)
    
    # Create a sample report
    sample_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Professional Consulting Services</title>
        <meta name="description" content="Expert business consulting">
    </head>
    <body>
        <h1>Transform Your Business</h1>
        <h2>Strategic Consulting</h2>
        <p>We help businesses optimize their operations and achieve sustainable growth through proven methodologies and expert guidance.</p>
        <img src="team.jpg" alt="consulting team">
        <h2>Our Approach</h2>
        <p>Our comprehensive approach includes market analysis, process optimization, and strategic planning tailored to your industry.</p>
        <a href="about.html">Learn More About Us</a>
        <a href="contact.html">Get In Touch</a>
    </body>
    </html>
    """
    
    try:
        seo_service = SEOService()
        result = seo_service.analyze_and_optimize_page(
            html_content=sample_html,
            page_title="Professional Consulting Services",
            business_type="consulting",
            target_location="Denver, CO"
        )
        
        # Save test results
        test_results = {
            "timestamp": datetime.now().isoformat(),
            "test_type": "SEO Service Validation",
            "seo_score": result['seo_score'],
            "seo_data": result['seo_data'],
            "trending_keywords": result['trending_keywords'],
            "recommendations": result['recommendations']
        }
        
        with open('seo_test_results.json', 'w') as f:
            json.dump(test_results, f, indent=2)
        
        print("✅ Test results saved to 'seo_test_results.json'")
        print(f"📊 Final SEO Score: {result['seo_score']['score']}/100")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to save test results: {e}")
        return False


def main():
    """Run all SEO service tests"""
    print("🚀 SEO Service Test Suite")
    print("=" * 50)
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Basic SEO Optimization", test_basic_seo_optimization),
        ("API Key Integration", test_with_api_keys),
        ("Multiple Business Types", test_multiple_business_types),
        ("Save Test Results", save_test_results)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"💥 {test_name}: ERROR - {e}")
    
    print(f"\n{'='*60}")
    print(f"🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! SEO Service is working correctly.")
        print("\n📋 Next Steps:")
        print("   1. Set up your API keys in .env file for enhanced features")
        print("   2. Test the service through the web interface")
        print("   3. Try converting a real Webflow export with SEO enabled")
    else:
        print("⚠️ Some tests failed. Check the error messages above.")
        print("\n🔧 Troubleshooting:")
        print("   1. Ensure all dependencies are installed: pip install -r requirements.txt")
        print("   2. Check that services/seo_service.py exists and is readable")
        print("   3. Verify Python path and import statements")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)