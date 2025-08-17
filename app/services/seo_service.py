import openai
import requests
import json
import re
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import time
from urllib.parse import quote
import os


class SEOService:
    def __init__(self, openai_api_key: str = None, serp_api_key: str = None):
        """
        Initialize SEO Service with API keys
        
        Args:
            openai_api_key: OpenAI API key for content generation
            serp_api_key: SerpAPI key for Google Trends data
        """
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        self.serp_api_key = serp_api_key or os.getenv('SERP_API_KEY')
        
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
    
    def analyze_and_optimize_page(self, html_content: str, page_title: str, 
                                 business_type: str = "", target_location: str = "") -> Dict:
        """
        Main function to analyze and optimize a page for SEO
        
        Args:
            html_content: The HTML content of the page
            page_title: Title of the page
            business_type: Type of business for targeting
            target_location: Geographic location for local SEO
            
        Returns:
            Dictionary containing optimized content and SEO data
        """
        print(f"🔍 Starting SEO analysis for page: {page_title}")
        
        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract current content
        page_analysis = self._analyze_current_content(soup, page_title)
        
        # Get trending keywords
        trending_keywords = self._get_trending_keywords(
            page_analysis['primary_topic'], 
            business_type, 
            target_location
        )
        
        # Generate SEO optimizations
        seo_optimization = self._generate_seo_optimization(
            page_analysis, 
            trending_keywords, 
            business_type, 
            target_location
        )
        
        # Inject SEO elements
        optimized_html = self._inject_seo_elements(soup, seo_optimization)
        
        # Calculate SEO score
        seo_score = self._calculate_seo_score(optimized_html, seo_optimization)
        
        return {
            'optimized_html': str(optimized_html),
            'seo_data': seo_optimization,
            'seo_score': seo_score,
            'trending_keywords': trending_keywords,
            'recommendations': self._generate_recommendations(seo_score)
        }
    
    def _analyze_current_content(self, soup: BeautifulSoup, page_title: str) -> Dict:
        """Analyze current page content to understand context"""
        
        # Extract text content
        text_content = soup.get_text(strip=True)
        
        # Get headings
        headings = {
            'h1': [h.get_text(strip=True) for h in soup.find_all('h1')],
            'h2': [h.get_text(strip=True) for h in soup.find_all('h2')],
            'h3': [h.get_text(strip=True) for h in soup.find_all('h3')]
        }
        
        # Extract images
        images = [
            {
                'src': img.get('src', ''),
                'alt': img.get('alt', ''),
                'title': img.get('title', '')
            }
            for img in soup.find_all('img')
        ]
        
        # Determine primary topic
        primary_topic = self._extract_primary_topic(page_title, headings, text_content)
        
        # Get word count
        word_count = len(text_content.split())
        
        return {
            'page_title': page_title,
            'primary_topic': primary_topic,
            'headings': headings,
            'text_content': text_content[:1000],  # First 1000 chars for analysis
            'word_count': word_count,
            'images': images,
            'has_meta_description': bool(soup.find('meta', attrs={'name': 'description'})),
            'has_title_tag': bool(soup.find('title'))
        }
    
    def _extract_primary_topic(self, title: str, headings: Dict, content: str) -> str:
        """Extract the primary topic from page content"""
        
        # Combine all text for analysis
        all_text = f"{title} {' '.join(headings.get('h1', []))} {' '.join(headings.get('h2', []))}"
        
        # Common words to ignore
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'about', 'services', 'home', 'page'}
        
        # Extract meaningful words
        words = re.findall(r'\b[a-zA-Z]{3,}\b', all_text.lower())
        words = [w for w in words if w not in stop_words]
        
        # Get most common words
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        if word_freq:
            primary_topic = max(word_freq, key=word_freq.get)
        else:
            primary_topic = title.lower().replace(' ', '_')
        
        return primary_topic
    
    def _get_trending_keywords(self, primary_topic: str, business_type: str, location: str) -> List[str]:
        """Get trending keywords using Google Trends API or fallback"""
        
        trending_keywords = []
        
        # Try Google Trends via SerpAPI
        if self.serp_api_key:
            try:
                trending_keywords = self._get_google_trends_keywords(primary_topic, location)
            except Exception as e:
                print(f"⚠️ Google Trends API error: {e}")
        
        # Fallback to predefined trending keywords
        if not trending_keywords:
            trending_keywords = self._get_fallback_trending_keywords(primary_topic, business_type, location)
        
        return trending_keywords[:10]  # Limit to top 10
    
    def _get_google_trends_keywords(self, topic: str, location: str = "") -> List[str]:
        """Get trending keywords from Google Trends via SerpAPI"""
        
        url = "https://serpapi.com/search.json"
        
        params = {
            "engine": "google_trends",
            "q": topic,
            "api_key": self.serp_api_key,
            "data_type": "RELATED_QUERIES"
        }
        
        if location:
            params["geo"] = location
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            related_queries = data.get("related_queries", {})
            trending = related_queries.get("rising", [])
            
            keywords = []
            for item in trending[:10]:
                if isinstance(item, dict) and 'query' in item:
                    keywords.append(item['query'])
                elif isinstance(item, str):
                    keywords.append(item)
            
            return keywords
        
        return []
    
    def _get_fallback_trending_keywords(self, topic: str, business_type: str, location: str) -> List[str]:
        """Fallback trending keywords based on business type and current trends"""
        
        # Current year for trending terms
        current_year = datetime.now().year
        
        # Base keywords related to topic
        base_keywords = [f"{topic} {current_year}", f"best {topic}", f"{topic} near me", f"{topic} services"]
        
        # Business type specific keywords
        business_keywords = {
            'restaurant': ['food delivery', 'takeout', 'dine in', 'menu', 'reservations'],
            'retail': ['online shopping', 'deals', 'sale', 'new arrivals', 'free shipping'],
            'service': ['professional', 'certified', 'expert', 'consultation', 'appointment'],
            'health': ['wellness', 'treatment', 'consultation', 'appointment', 'care'],
            'technology': ['digital', 'innovation', 'automation', 'AI', 'software'],
            'education': ['online learning', 'courses', 'training', 'certification', 'skills']
        }
        
        # Add business-specific keywords
        if business_type.lower() in business_keywords:
            base_keywords.extend([f"{topic} {kw}" for kw in business_keywords[business_type.lower()]])
        
        # Add location-based keywords
        if location:
            base_keywords.extend([
                f"{topic} in {location}",
                f"{location} {topic}",
                f"{business_type} {location}" if business_type else f"{topic} {location}"
            ])
        
        # Add current trending terms (2024/2025 specific)
        trending_terms = [
            'sustainable', 'eco-friendly', 'digital transformation', 'AI-powered',
            'contactless', 'virtual', 'personalized', 'innovative', 'smart'
        ]
        
        base_keywords.extend([f"{topic} {term}" for term in trending_terms])
        
        return base_keywords[:15]
    
    def _generate_seo_optimization(self, page_analysis: Dict, trending_keywords: List[str], 
                                  business_type: str, location: str) -> Dict:
        """Generate SEO optimizations using OpenAI"""
        
        if not self.openai_api_key:
            return self._generate_fallback_seo_optimization(page_analysis, trending_keywords, business_type, location)
        
        try:
            # Create prompt for OpenAI
            prompt = self._create_seo_prompt(page_analysis, trending_keywords, business_type, location)
            
            # Generate SEO content
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert SEO specialist with deep knowledge of current SEO best practices, Google algorithm updates, and trending optimization techniques."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            seo_content = response.choices[0].message.content
            
            # Parse the response
            return self._parse_openai_seo_response(seo_content, page_analysis, trending_keywords)
            
        except Exception as e:
            print(f"⚠️ OpenAI API error: {e}")
            return self._generate_fallback_seo_optimization(page_analysis, trending_keywords, business_type, location)
    
    def _create_seo_prompt(self, page_analysis: Dict, trending_keywords: List[str], 
                          business_type: str, location: str) -> str:
        """Create prompt for OpenAI SEO optimization"""
        
        return f"""
As an SEO expert, optimize this webpage for search engines using current best practices and trending keywords.

PAGE INFORMATION:
- Title: {page_analysis['page_title']}
- Primary Topic: {page_analysis['primary_topic']}
- Business Type: {business_type or 'General'}
- Location: {location or 'Not specified'}
- Current Content: {page_analysis['text_content'][:500]}...
- Word Count: {page_analysis['word_count']}

TRENDING KEYWORDS TO INCORPORATE:
{', '.join(trending_keywords)}

Please provide the following optimizations in JSON format:

{{
    "meta_title": "SEO-optimized title (50-60 characters)",
    "meta_description": "Compelling meta description (150-160 characters)",
    "focus_keywords": ["primary keyword", "secondary keyword", "long-tail keyword"],
    "schema_type": "appropriate schema.org type",
    "og_title": "Open Graph title",
    "og_description": "Open Graph description",
    "suggested_headings": ["H1 suggestion", "H2 suggestion", "H2 suggestion"],
    "alt_text_suggestions": ["alt text for main image", "alt text for secondary image"],
    "internal_link_suggestions": ["About Us", "Services", "Contact"],
    "content_suggestions": "Brief suggestions for improving content for SEO"
}}

Focus on:
1. Including trending keywords naturally
2. Local SEO if location is provided
3. Current SEO best practices for 2024/2025
4. User intent optimization
5. E-A-T (Expertise, Authoritativeness, Trustworthiness)
"""
    
    def _parse_openai_seo_response(self, response: str, page_analysis: Dict, trending_keywords: List[str]) -> Dict:
        """Parse OpenAI response into structured SEO data"""
        
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                seo_data = json.loads(json_match.group())
                
                # Validate and enhance the data
                return {
                    'meta_title': seo_data.get('meta_title', page_analysis['page_title'])[:60],
                    'meta_description': seo_data.get('meta_description', '')[:160],
                    'focus_keywords': seo_data.get('focus_keywords', trending_keywords[:3]),
                    'schema_type': seo_data.get('schema_type', 'WebPage'),
                    'og_title': seo_data.get('og_title', seo_data.get('meta_title', page_analysis['page_title'])),
                    'og_description': seo_data.get('og_description', seo_data.get('meta_description', '')),
                    'suggested_headings': seo_data.get('suggested_headings', []),
                    'alt_text_suggestions': seo_data.get('alt_text_suggestions', []),
                    'internal_link_suggestions': seo_data.get('internal_link_suggestions', []),
                    'content_suggestions': seo_data.get('content_suggestions', ''),
                    'trending_keywords_used': trending_keywords
                }
        except json.JSONDecodeError:
            pass
        
        # Fallback if JSON parsing fails
        return self._generate_fallback_seo_optimization(page_analysis, trending_keywords, "", "")
    
    def _generate_fallback_seo_optimization(self, page_analysis: Dict, trending_keywords: List[str],
                                          business_type: str, location: str) -> Dict:
        """Generate SEO optimization without OpenAI"""
        
        primary_topic = page_analysis['primary_topic']
        page_title = page_analysis['page_title']
        
        # Generate meta title
        location_part = f" in {location}" if location else ""
        meta_title = f"{page_title} | {primary_topic.title()}{location_part}"
        if len(meta_title) > 60:
            meta_title = f"{primary_topic.title()}{location_part} | {page_title}"[:60]
        
        # Generate meta description
        trending_phrase = trending_keywords[0] if trending_keywords else primary_topic
        meta_description = f"Discover the best {primary_topic} services{location_part}. {trending_phrase} with expert quality and professional results. Contact us today!"
        meta_description = meta_description[:160]
        
        # Focus keywords
        focus_keywords = [
            primary_topic,
            f"{primary_topic} {location}".strip() if location else f"best {primary_topic}",
            trending_keywords[0] if trending_keywords else f"{primary_topic} services"
        ]
        
        return {
            'meta_title': meta_title,
            'meta_description': meta_description,
            'focus_keywords': focus_keywords,
            'schema_type': self._determine_schema_type(business_type, page_title),
            'og_title': meta_title,
            'og_description': meta_description,
            'suggested_headings': [
                f"Professional {primary_topic.title()} Services{location_part}",
                f"Why Choose Our {primary_topic.title()} Services",
                f"Get Started with {primary_topic.title()} Today"
            ],
            'alt_text_suggestions': [
                f"Professional {primary_topic} service",
                f"{primary_topic} results showcase",
                f"Expert {primary_topic} team"
            ],
            'internal_link_suggestions': ["About Us", "Services", "Contact", "Portfolio"],
            'content_suggestions': f"Add more content about {', '.join(trending_keywords[:3])} to improve SEO relevance.",
            'trending_keywords_used': trending_keywords
        }
    
    def _determine_schema_type(self, business_type: str, page_title: str) -> str:
        """Determine appropriate Schema.org type"""
        
        schema_mapping = {
            'restaurant': 'Restaurant',
            'hotel': 'Hotel',
            'service': 'LocalBusiness',
            'retail': 'Store',
            'health': 'MedicalBusiness',
            'law': 'LegalService',
            'real estate': 'RealEstateAgent',
            'education': 'EducationalOrganization',
            'technology': 'TechCompany',
            'consulting': 'ProfessionalService'
        }
        
        business_lower = business_type.lower()
        title_lower = page_title.lower()
        
        for key, schema in schema_mapping.items():
            if key in business_lower or key in title_lower:
                return schema
        
        # Check specific page types
        if any(word in title_lower for word in ['about', 'team', 'company']):
            return 'AboutPage'
        elif any(word in title_lower for word in ['contact', 'location']):
            return 'ContactPage'
        elif any(word in title_lower for word in ['service', 'product']):
            return 'Service'
        elif 'blog' in title_lower or 'article' in title_lower:
            return 'Article'
        
        return 'WebPage'
    
    def _inject_seo_elements(self, soup: BeautifulSoup, seo_data: Dict) -> BeautifulSoup:
        """Inject SEO elements into HTML"""
        
        # Ensure head tag exists
        head = soup.find('head')
        if not head:
            head = soup.new_tag('head')
            if soup.html:
                soup.html.insert(0, head)
            else:
                soup.insert(0, head)
        
        # Update or add title tag
        title_tag = head.find('title')
        if title_tag:
            title_tag.string = seo_data['meta_title']
        else:
            title_tag = soup.new_tag('title')
            title_tag.string = seo_data['meta_title']
            head.append(title_tag)
        
        # Update or add meta description
        meta_desc = head.find('meta', attrs={'name': 'description'})
        if meta_desc:
            meta_desc['content'] = seo_data['meta_description']
        else:
            meta_desc = soup.new_tag('meta', attrs={'name': 'description', 'content': seo_data['meta_description']})
            head.append(meta_desc)
        
        # Add meta keywords
        keywords_content = ', '.join(seo_data['focus_keywords'])
        meta_keywords = head.find('meta', attrs={'name': 'keywords'})
        if meta_keywords:
            meta_keywords['content'] = keywords_content
        else:
            meta_keywords = soup.new_tag('meta', attrs={'name': 'keywords', 'content': keywords_content})
            head.append(meta_keywords)
        
        # Add Open Graph tags
        self._add_open_graph_tags(head, soup, seo_data)
        
        # Add Twitter Card tags
        self._add_twitter_card_tags(head, soup, seo_data)
        
        # Add Schema.org markup
        self._add_schema_markup(head, soup, seo_data)
        
        # Add additional SEO meta tags
        self._add_additional_meta_tags(head, soup)
        
        # Optimize images
        self._optimize_image_alt_tags(soup, seo_data)
        
        return soup
    
    def _add_open_graph_tags(self, head: BeautifulSoup, soup: BeautifulSoup, seo_data: Dict):
        """Add Open Graph meta tags"""
        
        og_tags = [
            ('og:title', seo_data['og_title']),
            ('og:description', seo_data['og_description']),
            ('og:type', 'website'),
            ('og:locale', 'en_US')
        ]
        
        for property_name, content in og_tags:
            existing_tag = head.find('meta', attrs={'property': property_name})
            if existing_tag:
                existing_tag['content'] = content
            else:
                og_tag = soup.new_tag('meta', attrs={'property': property_name, 'content': content})
                head.append(og_tag)
    
    def _add_twitter_card_tags(self, head: BeautifulSoup, soup: BeautifulSoup, seo_data: Dict):
        """Add Twitter Card meta tags"""
        
        twitter_tags = [
            ('twitter:card', 'summary_large_image'),
            ('twitter:title', seo_data['og_title']),
            ('twitter:description', seo_data['og_description'])
        ]
        
        for name, content in twitter_tags:
            existing_tag = head.find('meta', attrs={'name': name})
            if existing_tag:
                existing_tag['content'] = content
            else:
                twitter_tag = soup.new_tag('meta', attrs={'name': name, 'content': content})
                head.append(twitter_tag)
    
    def _add_schema_markup(self, head: BeautifulSoup, soup: BeautifulSoup, seo_data: Dict):
        """Add Schema.org JSON-LD markup"""
        
        schema_data = {
            "@context": "https://schema.org",
            "@type": seo_data['schema_type'],
            "name": seo_data['meta_title'],
            "description": seo_data['meta_description']
        }
        
        # Add additional schema properties based on type
        if seo_data['schema_type'] in ['LocalBusiness', 'Restaurant', 'Store']:
            schema_data.update({
                "@type": seo_data['schema_type'],
                "url": "<?php echo home_url(); ?>",
                "telephone": "<?php echo get_option('business_phone', ''); ?>",
                "address": {
                    "@type": "PostalAddress",
                    "addressLocality": "<?php echo get_option('business_city', ''); ?>",
                    "addressRegion": "<?php echo get_option('business_state', ''); ?>",
                    "addressCountry": "<?php echo get_option('business_country', 'US'); ?>"
                }
            })
        
        # Create script tag with JSON-LD
        script_tag = soup.new_tag('script', attrs={'type': 'application/ld+json'})
        script_tag.string = json.dumps(schema_data, indent=2)
        head.append(script_tag)
    
    def _add_additional_meta_tags(self, head: BeautifulSoup, soup: BeautifulSoup):
        """Add additional SEO meta tags"""
        
        additional_tags = [
            ('robots', 'index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1'),
            ('googlebot', 'index, follow'),
            ('bingbot', 'index, follow'),
            ('viewport', 'width=device-width, initial-scale=1'),
            ('theme-color', '#000000'),
            ('format-detection', 'telephone=no')
        ]
        
        for name, content in additional_tags:
            existing_tag = head.find('meta', attrs={'name': name})
            if not existing_tag:
                meta_tag = soup.new_tag('meta', attrs={'name': name, 'content': content})
                head.append(meta_tag)
    
    def _optimize_image_alt_tags(self, soup: BeautifulSoup, seo_data: Dict):
        """Optimize image alt tags for SEO"""
        
        images = soup.find_all('img')
        alt_suggestions = seo_data.get('alt_text_suggestions', [])
        focus_keywords = seo_data.get('focus_keywords', [])
        
        for i, img in enumerate(images):
            current_alt = img.get('alt', '')
            
            if not current_alt or current_alt.strip() == '':
                # Generate alt text
                if i < len(alt_suggestions):
                    new_alt = alt_suggestions[i]
                elif focus_keywords:
                    keyword = focus_keywords[i % len(focus_keywords)]
                    new_alt = f"Professional {keyword} service image"
                else:
                    new_alt = f"Image {i + 1}"
                
                img['alt'] = new_alt
            elif len(current_alt) < 50:
                # Enhance existing alt text
                if focus_keywords and not any(kw in current_alt.lower() for kw in focus_keywords):
                    keyword = focus_keywords[0]
                    img['alt'] = f"{current_alt} - {keyword}"
    
    def _calculate_seo_score(self, soup: BeautifulSoup, seo_data: Dict) -> Dict:
        """Calculate SEO score based on various factors"""
        
        score = 0
        max_score = 100
        details = {}
        
        # Title tag (10 points)
        title_tag = soup.find('title')
        if title_tag and title_tag.string:
            title_length = len(title_tag.string)
            if 30 <= title_length <= 60:
                score += 10
                details['title'] = {'score': 10, 'status': 'Good', 'message': 'Title length is optimal'}
            elif title_length > 0:
                score += 5
                details['title'] = {'score': 5, 'status': 'Fair', 'message': f'Title length ({title_length}) should be 30-60 characters'}
            else:
                details['title'] = {'score': 0, 'status': 'Poor', 'message': 'Title is empty'}
        else:
            details['title'] = {'score': 0, 'status': 'Poor', 'message': 'Missing title tag'}
        
        # Meta description (10 points)
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            desc_length = len(meta_desc['content'])
            if 120 <= desc_length <= 160:
                score += 10
                details['meta_description'] = {'score': 10, 'status': 'Good', 'message': 'Meta description length is optimal'}
            elif desc_length > 0:
                score += 5
                details['meta_description'] = {'score': 5, 'status': 'Fair', 'message': f'Meta description length ({desc_length}) should be 120-160 characters'}
        else:
            details['meta_description'] = {'score': 0, 'status': 'Poor', 'message': 'Missing meta description'}
        
        # Headings structure (15 points)
        h1_tags = soup.find_all('h1')
        h2_tags = soup.find_all('h2')
        heading_score = 0
        
        if len(h1_tags) == 1:
            heading_score += 8
        elif len(h1_tags) > 1:
            heading_score += 3
        
        if len(h2_tags) >= 2:
            heading_score += 7
        elif len(h2_tags) == 1:
            heading_score += 4
        
        score += heading_score
        details['headings'] = {
            'score': heading_score,
            'status': 'Good' if heading_score >= 12 else 'Fair' if heading_score >= 7 else 'Poor',
            'message': f'H1: {len(h1_tags)}, H2: {len(h2_tags)} (optimal: 1 H1, 2+ H2)'
        }
        
        # Image optimization (10 points)
        images = soup.find_all('img')
        images_with_alt = [img for img in images if img.get('alt')]
        
        if len(images) == 0:
            image_score = 5  # No images, neutral
        else:
            alt_percentage = (len(images_with_alt) / len(images)) * 100
            if alt_percentage == 100:
                image_score = 10
            elif alt_percentage >= 80:
                image_score = 7
            elif alt_percentage >= 50:
                image_score = 4
            else:
                image_score = 1
        
        score += image_score
        details['images'] = {
            'score': image_score,
            'status': 'Good' if image_score >= 8 else 'Fair' if image_score >= 5 else 'Poor',
            'message': f'{len(images_with_alt)}/{len(images)} images have alt text'
        }
        
        # Content length (10 points)
        text_content = soup.get_text(strip=True)
        word_count = len(text_content.split())
        
        if word_count >= 300:
            content_score = 10
        elif word_count >= 150:
            content_score = 6
        elif word_count >= 50:
            content_score = 3
        else:
            content_score = 0
        
        score += content_score
        details['content_length'] = {
            'score': content_score,
            'status': 'Good' if content_score >= 8 else 'Fair' if content_score >= 5 else 'Poor',
            'message': f'{word_count} words (recommended: 300+)'
        }
        
        # Schema markup (10 points)
        schema_script = soup.find('script', attrs={'type': 'application/ld+json'})
        if schema_script:
            score += 10
            details['schema'] = {'score': 10, 'status': 'Good', 'message': 'Schema markup present'}
        else:
            details['schema'] = {'score': 0, 'status': 'Poor', 'message': 'Missing schema markup'}
        
        # Open Graph tags (10 points)
        og_title = soup.find('meta', attrs={'property': 'og:title'})
        og_desc = soup.find('meta', attrs={'property': 'og:description'})
        
        og_score = 0
        if og_title:
            og_score += 5
        if og_desc:
            og_score += 5
        
        score += og_score
        details['open_graph'] = {
            'score': og_score,
            'status': 'Good' if og_score >= 8 else 'Fair' if og_score >= 5 else 'Poor',
            'message': f'Open Graph tags: {og_score}/10 points'
        }
        
        # Mobile viewport (5 points)
        viewport = soup.find('meta', attrs={'name': 'viewport'})
        if viewport:
            score += 5
            details['mobile'] = {'score': 5, 'status': 'Good', 'message': 'Mobile viewport configured'}
        else:
            details['mobile'] = {'score': 0, 'status': 'Poor', 'message': 'Missing mobile viewport'}
        
        # Keyword usage (10 points)
        focus_keywords = seo_data.get('focus_keywords', [])
        keyword_score = 0
        
        if focus_keywords:
            title_text = (title_tag.string if title_tag and title_tag.string else '').lower()
            content_text = text_content.lower()
            
            keywords_in_title = sum(1 for kw in focus_keywords if kw.lower() in title_text)
            keywords_in_content = sum(1 for kw in focus_keywords if kw.lower() in content_text)
            
            keyword_score = min(10, (keywords_in_title * 3) + (keywords_in_content * 2))
        
        score += keyword_score
        details['keywords'] = {
            'score': keyword_score,
            'status': 'Good' if keyword_score >= 8 else 'Fair' if keyword_score >= 5 else 'Poor',
            'message': f'Focus keywords usage: {keyword_score}/10 points'
        }
        
        # Internal links (10 points)
        internal_links = soup.find_all('a', href=True)
        internal_link_count = len([link for link in internal_links if not link['href'].startswith('http')])
        
        if internal_link_count >= 3:
            link_score = 10
        elif internal_link_count >= 1:
            link_score = 6
        else:
            link_score = 0
        
        score += link_score
        details['internal_links'] = {
            'score': link_score,
            'status': 'Good' if link_score >= 8 else 'Fair' if link_score >= 5 else 'Poor',
            'message': f'{internal_link_count} internal links (recommended: 3+)'
        }
        
        # Calculate final score percentage
        final_score = round((score / max_score) * 100)
        
        # Determine overall status
        if final_score >= 80:
            status = 'Excellent'
            color = '#22c55e'
        elif final_score >= 60:
            status = 'Good'
            color = '#3b82f6'
        elif final_score >= 40:
            status = 'Fair'
            color = '#f59e0b'
        else:
            status = 'Poor'
            color = '#ef4444'
        
        return {
            'score': final_score,
            'status': status,
            'color': color,
            'details': details,
            'raw_score': score,
            'max_score': max_score
        }
    
    def _generate_recommendations(self, seo_score: Dict) -> List[str]:
        """Generate SEO improvement recommendations"""
        
        recommendations = []
        
        for category, data in seo_score['details'].items():
            if data['score'] < 8:  # If not excellent
                if category == 'title':
                    recommendations.append("Optimize title tag length (30-60 characters) and include focus keywords")
                elif category == 'meta_description':
                    recommendations.append("Write compelling meta description (120-160 characters) with call-to-action")
                elif category == 'headings':
                    recommendations.append("Improve heading structure: use one H1 and multiple H2 tags")
                elif category == 'images':
                    recommendations.append("Add descriptive alt text to all images for better accessibility and SEO")
                elif category == 'content_length':
                    recommendations.append("Increase content length to 300+ words for better search rankings")
                elif category == 'schema':
                    recommendations.append("Add Schema.org markup to help search engines understand your content")
                elif category == 'open_graph':
                    recommendations.append("Add Open Graph tags for better social media sharing")
                elif category == 'mobile':
                    recommendations.append("Add mobile viewport meta tag for mobile optimization")
                elif category == 'keywords':
                    recommendations.append("Better integrate focus keywords naturally throughout content")
                elif category == 'internal_links':
                    recommendations.append("Add more internal links to improve site navigation and SEO")
        
        # Add general recommendations based on overall score
        if seo_score['score'] < 60:
            recommendations.insert(0, "Consider comprehensive SEO audit - multiple areas need improvement")
        elif seo_score['score'] < 80:
            recommendations.append("Great progress! Focus on the remaining items to achieve excellent SEO")
        
        return recommendations[:5]  # Limit to top 5 recommendations