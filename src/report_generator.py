"""
Report generation module.

Creates comprehensive HTML reports with embedded maps and statistics.

Copyright (c) 2024-2026 e2kd7n
Licensed under the MIT License - see LICENSE file for details.
"""

import logging
import base64
import csv
import json
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Dict, Any, List
from xml.etree import ElementTree as ET

# QR code temporarily disabled - needs debugging before re-enabling
# TODO (#45): Debug QR code generation and scanning functionality
try:
    import qrcode
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False
    qrcode = None

from jinja2 import Template

try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError) as e:
    WEASYPRINT_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning(f"WeasyPrint not available: {e}. PDF export will be disabled.")
    HTML = None

from .units import UnitConverter

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates HTML reports from analysis results."""
    
    def __init__(self, analysis_results: Dict[str, Any]):
        """
        Initialize report generator.
        
        Args:
            analysis_results: Dictionary containing all analysis results
        """
        self.results = analysis_results
        self.template_dir = Path("templates")
        
        # Initialize unit converter
        config = analysis_results.get('config')
        unit_system = config.get('units.system', 'metric') if config else 'metric'
        self.units = UnitConverter(unit_system)
        
    def generate_report(self, output_path: str, generate_pdf: bool = False) -> None:
        """
        Generate complete HTML report.
        
        Args:
            output_path: Path to save the report
            generate_pdf: Whether to generate PDF report (default: False)
        """
        logger.info("Generating HTML report...")
        
        # Prepare context
        context = self._prepare_context()
        
        # QR code temporarily disabled - needs debugging
        # Generate QR code for mobile access only if available
        if QRCODE_AVAILABLE:
            qr_code_data = self._generate_qr_code(output_path)
            context['qr_code'] = qr_code_data
        else:
            context['qr_code'] = None
        
        # Render template
        html = self._render_template(context)
        
        # Save report
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        logger.info(f"Report saved to {output_path}")
        
        # Generate PDF version if requested
        if generate_pdf:
            pdf_path = str(output_file).replace('.html', '.pdf')
            try:
                self.generate_pdf(output_path, pdf_path)
                logger.info(f"PDF report saved to {pdf_path}")
            except Exception as e:
                print(f"\n\033[93m⚠️  WARNING\033[0m - Failed to generate PDF: {e}\n")
                logger.warning(f"Failed to generate PDF: {e}")
        
        # Generate data exports
        base_path = str(output_file).replace('.html', '')
        try:
            self.export_data(base_path)
            logger.info(f"Data exports saved to {base_path}_*.{{json,csv,gpx}}")
        except Exception as e:
            print(f"\n\033[93m⚠️  WARNING\033[0m - Failed to generate data exports: {e}\n")
            logger.warning(f"Failed to generate data exports: {e}")
    
    def _generate_qr_code(self, report_path: str) -> str | None:
        """
        Generate QR code for mobile access to the report.
        
        NOTE: QR code functionality is currently disabled and needs debugging.
        
        Args:
            report_path: Path to the report file
            
        Returns:
            Base64-encoded PNG image data URL or None if qrcode not available
        """
        if not QRCODE_AVAILABLE:
            logger.warning("QR code generation skipped - qrcode module not available")
            return None
            
        try:
            # Convert to absolute path for file:// URL
            abs_path = Path(report_path).resolve()
            file_url = f"file://{abs_path}"
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(file_url)
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_str}"
        except Exception as e:
            logger.warning(f"Failed to generate QR code: {e}")
            return ""
    
    def generate_pdf(self, html_path: str, pdf_path: str) -> None:
        """
        Generate PDF version of the HTML report.
        
        Args:
            html_path: Path to the HTML report
            pdf_path: Path to save the PDF
        """
        if not WEASYPRINT_AVAILABLE:
            logger.warning("PDF generation skipped: WeasyPrint not available. Install system dependencies: brew install pango")
            return
            
        try:
            # Read HTML content
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Create PDF-optimized version (remove interactive elements)
            pdf_html = self._prepare_pdf_html(html_content)
            
            # Generate PDF
            HTML(string=pdf_html).write_pdf(pdf_path)
            logger.info(f"PDF generated successfully: {pdf_path}")
            
        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            raise
    
    def _prepare_pdf_html(self, html_content: str) -> str:
        """
        Prepare HTML content for PDF export by removing interactive elements.
        
        Args:
            html_content: Original HTML content
            
        Returns:
            PDF-optimized HTML content
        """
        # Remove interactive JavaScript elements
        pdf_html = html_content
        
        # Remove refresh button
        pdf_html = pdf_html.replace('onclick="refreshReport()"', '')
        
        # Add PDF-specific styles
        pdf_styles = """
        <style>
            @page { size: A4; margin: 1cm; }
            body { font-size: 10pt; }
            .no-print { display: none !important; }
            .map-container { page-break-inside: avoid; }
            .card { page-break-inside: avoid; }
        </style>
        """
        pdf_html = pdf_html.replace('</head>', f'{pdf_styles}</head>')
        
        return pdf_html
    
    def export_data(self, base_path: str) -> None:
        """
        Export route data in multiple formats.
        
        Args:
            base_path: Base path for export files (without extension)
        """
        # Export JSON
        self._export_json(f"{base_path}_routes.json")
        
        # Export CSV
        self._export_csv(f"{base_path}_routes.csv")
        
        # Export GPX
        self._export_gpx(f"{base_path}_routes.gpx")
    
    def _export_json(self, output_path: str) -> None:
        """Export route data as JSON."""
        export_data = {
            'timestamp': datetime.now().isoformat(),
            'routes': [],
            'statistics': self.results.get('statistics', {}),
            'recommendations': self.results.get('recommendations', {})
        }
        
        # Add route data
        for group, score, breakdown in self.results.get('ranked_routes', []):
            metrics = self.results.get('optimizer').metrics.get(group.id)
            route_data = {
                'id': group.id,
                'direction': group.direction,
                'score': score,
                'frequency': group.frequency,
                'avg_duration_min': (metrics.avg_duration / 60) if metrics else None,
                'avg_distance': metrics.avg_distance if metrics else None,
                'avg_speed': metrics.avg_speed if metrics else None,
                'coordinates': group.representative_route.coordinates if group.representative_route else None,
                'breakdown': breakdown
            }
            export_data['routes'].append(route_data)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2)
    
    def _export_csv(self, output_path: str) -> None:
        """Export route data as CSV."""
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow([
                'Route ID', 'Direction', 'Score', 'Frequency',
                'Avg Duration (min)', 'Avg Distance', 'Avg Speed',
                'Weather Score', 'Safety Score', 'Efficiency Score'
            ])
            
            # Write route data
            for group, score, breakdown in self.results.get('ranked_routes', []):
                metrics = self.results.get('optimizer').metrics.get(group.id)
                writer.writerow([
                    group.id,
                    group.direction,
                    f"{score:.1f}",
                    group.frequency,
                    f"{(metrics.avg_duration / 60):.1f}" if metrics else 'N/A',
                    f"{metrics.avg_distance:.2f}" if metrics else 'N/A',
                    f"{metrics.avg_speed:.1f}" if metrics else 'N/A',
                    f"{breakdown.get('weather', 0):.1f}",
                    f"{breakdown.get('safety', 0):.1f}",
                    f"{breakdown.get('efficiency', 0):.1f}"
                ])
    
    def _export_gpx(self, output_path: str) -> None:
        """Export route data as GPX."""
        # Create GPX root element
        gpx = ET.Element('gpx', {
            'version': '1.1',
            'creator': 'Strava Commute Analyzer',
            'xmlns': 'http://www.topografix.com/GPX/1/1'
        })
        
        # Add metadata
        metadata = ET.SubElement(gpx, 'metadata')
        ET.SubElement(metadata, 'time').text = datetime.now().isoformat()
        
        # Add routes
        for group, score, breakdown in self.results.get('ranked_routes', []):
            if not group.representative_route or not group.representative_route.coordinates:
                continue
            
            # Create route element
            rte = ET.SubElement(gpx, 'rte')
            ET.SubElement(rte, 'name').text = group.id
            ET.SubElement(rte, 'desc').text = f"Score: {score:.1f}, Direction: {group.direction}"
            
            # Add route points
            for lat, lon in group.representative_route.coordinates:
                rtept = ET.SubElement(rte, 'rtept', {
                    'lat': str(lat),
                    'lon': str(lon)
                })
        
        # Write GPX file
        tree = ET.ElementTree(gpx)
        ET.indent(tree, space='  ')
        tree.write(output_path, encoding='utf-8', xml_declaration=True)
    
    def _prepare_context(self) -> Dict[str, Any]:
        """
        Prepare template context from analysis results.
        
        Returns:
            Dictionary with template variables
        """
        recommendations = self.results.get('recommendations', {})
        optimal = recommendations.get('optimal', {})
        alternative = recommendations.get('alternative')
        
        # Get route names and colors from visualizer
        visualizer = self.results.get('visualizer')
        route_names = visualizer.get_route_names() if visualizer else {}
        route_colors = visualizer.get_route_colors() if visualizer else {}
        
        # Get current weather for general location (use home location)
        current_weather = None
        home = self.results.get('home')
        if home:
            from .weather_fetcher import WeatherFetcher
            weather_fetcher = WeatherFetcher()
            current_weather = weather_fetcher.get_current_conditions(home.lat, home.lon)
        
        # Prepare ranked routes with metrics, names, Strava links, and current weather
        ranked_routes = []
        for group, score, breakdown in self.results.get('ranked_routes', []):
            metrics = self.results.get('optimizer').metrics.get(group.id)
            route_name = route_names.get(group.id, group.id)
            
            # Get most recent activity ID for this route group
            most_recent_activity_id = None
            if group.routes:
                # Sort by timestamp to get most recent
                sorted_routes = sorted(group.routes, key=lambda r: r.timestamp, reverse=True)
                most_recent_activity_id = sorted_routes[0].activity_id
            
            # Get current weather details from breakdown if available
            current_route_weather = breakdown.get('weather_details')
            
            ranked_routes.append({
                'group': group,
                'score': score,
                'breakdown': breakdown,
                'metrics': metrics,
                'name': route_name,
                'color': route_colors.get(group.id, '#808080'),  # Default to gray if not found
                'strava_url': f"https://www.strava.com/activities/{most_recent_activity_id}" if most_recent_activity_id else None,
                'current_weather': current_route_weather,
                'is_plus_route': group.is_plus_route  # Flag for extended/recreational routes
            })
        
        # Calculate statistics
        total_activities = len(self.results.get('all_activities', []))
        commute_activities = len(self.results.get('commute_activities', []))
        route_variants = len(self.results.get('route_groups', []))
        
        # Get date range
        activities = self.results.get('all_activities', [])
        if activities:
            dates = [a.start_date for a in activities]
            date_range = f"{min(dates)[:10]} to {max(dates)[:10]}"
        else:
            date_range = "N/A"
        
        # Prepare long rides data
        long_rides = self.results.get('long_rides', [])
        long_rides_stats = {}
        distance_bins = []
        
        if long_rides:
            distances = [r.distance_km for r in long_rides]
            loop_count = sum(1 for r in long_rides if r.is_loop)
            
            # Calculate distance distribution bins (10 unit intervals)
            min_dist = min(distances)
            max_dist = max(distances)
            bin_size = 10  # 10 unit bins
            num_bins = int((max_dist - min_dist) / bin_size) + 1
            
            # Create bins
            bins = {}
            dist_unit = self.units.distance_unit()
            for i in range(num_bins):
                bin_start = int(min_dist / bin_size) * bin_size + i * bin_size
                bin_end = bin_start + bin_size
                bin_label = f"{bin_start}-{bin_end}{dist_unit}"
                bins[bin_label] = 0
            
            # Count rides in each bin
            for dist in distances:
                bin_index = int((dist - (int(min_dist / bin_size) * bin_size)) / bin_size)
                bin_start = int(min_dist / bin_size) * bin_size + bin_index * bin_size
                bin_end = bin_start + bin_size
                bin_label = f"{bin_start}-{bin_end}{dist_unit}"
                if bin_label in bins:
                    bins[bin_label] += 1
            
            distance_bins = [{'label': k, 'count': v} for k, v in bins.items()]
            
            long_rides_stats = {
                'total_rides': len(long_rides),
                'total_distance': sum(distances),
                'avg_distance': sum(distances) / len(distances),
                'min_distance': min(distances),
                'max_distance': max(distances),
                'distance_unit': dist_unit,
                'loop_count': loop_count,
                'loop_percentage': (loop_count / len(long_rides)) * 100,
                'point_to_point_count': len(long_rides) - loop_count
            }
        
        context = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'optimal': optimal,
            'alternative': alternative,
            'ranked_routes': ranked_routes,
            'map_html': self.results.get('map_html', ''),
            'preview_map_html': self.results.get('preview_map_html', ''),
            'home': self.results.get('home'),
            'work': self.results.get('work'),
            'route_names': route_names,
            'current_weather': current_weather,  # Add current weather for general location
            'statistics': {
                'total_activities': total_activities,
                'commute_activities': commute_activities,
                'route_variants': route_variants,
                'date_range': date_range
            },
            'long_rides': long_rides,
            'long_rides_stats': long_rides_stats,
            'distance_bins': distance_bins,
            'units': self.units  # Pass unit converter to template
        }
        
        return context
    
    def _render_template(self, context: Dict[str, Any]) -> str:
        """
        Render HTML template with context.
        
        Args:
            context: Template context dictionary
            
        Returns:
            Rendered HTML string
        """
        # Load template from external file
        template_path = self.template_dir / "report_template.html"
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template_str = f.read()
        
        template = Template(template_str)
        return template.render(**context)

# Made with Bob
