import json
from datetime import datetime, timedelta
import logging
import calendar

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_sleep_data(json_file):
    """Load sleep data from JSON file"""
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_all_years_data(sleep_data):
    """Get all sleep records"""
    return sorted(sleep_data['sleeps'], key=lambda x: x['fromTime'], reverse=True)

def get_monthly_averages(sleep_records):
    """Calculate monthly averages for sleep metrics"""
    monthly_data = {}
    for record in sleep_records:
        date = datetime.fromtimestamp(record['fromTime'] / 1000)
        month_key = f"{date.year}-{date.month:02d}"
        
        if month_key not in monthly_data:
            monthly_data[month_key] = {
                'count': 0,
                'hours': 0,
                'rating': 0,
                'deepSleep': 0,
                'cycles': 0
            }
        
        monthly_data[month_key]['count'] += 1
        monthly_data[month_key]['hours'] += record['hours']
        monthly_data[month_key]['rating'] += record['rating']
        monthly_data[month_key]['deepSleep'] += record['deepSleep']
        monthly_data[month_key]['cycles'] += record['cycles']
    
    # Calculate averages
    for month_key in monthly_data:
        count = monthly_data[month_key]['count']
        monthly_data[month_key]['hours'] /= count
        monthly_data[month_key]['rating'] /= count
        monthly_data[month_key]['deepSleep'] /= count
        monthly_data[month_key]['cycles'] /= count
    
    return monthly_data

def get_yearly_averages(sleep_records):
    """Calculate yearly averages for sleep metrics"""
    yearly_data = {}
    for record in sleep_records:
        date = datetime.fromtimestamp(record['fromTime'] / 1000)
        year_key = str(date.year)
        
        if year_key not in yearly_data:
            yearly_data[year_key] = {
                'count': 0,
                'hours': 0,
                'rating': 0,
                'deepSleep': 0,
                'cycles': 0
            }
        
        yearly_data[year_key]['count'] += 1
        yearly_data[year_key]['hours'] += record['hours']
        yearly_data[year_key]['rating'] += record['rating']
        yearly_data[year_key]['deepSleep'] += record['deepSleep']
        yearly_data[year_key]['cycles'] += record['cycles']
    
    # Calculate averages
    for year_key in yearly_data:
        count = yearly_data[year_key]['count']
        yearly_data[year_key]['hours'] /= count
        yearly_data[year_key]['rating'] /= count
        yearly_data[year_key]['deepSleep'] /= count
        yearly_data[year_key]['cycles'] /= count
    
    return yearly_data

def get_seasonal_averages(sleep_records):
    """Calculate seasonal averages for sleep metrics"""
    seasonal_data = {}
    for record in sleep_records:
        date = datetime.fromtimestamp(record['fromTime'] / 1000)
        month = date.month
        if 3 <= month <= 5:
            season = 'Spring'
        elif 6 <= month <= 8:
            season = 'Summer'
        elif 9 <= month <= 11:
            season = 'Fall'
        else:
            season = 'Winter'
        
        season_key = f"{date.year}-{season}"
        
        if season_key not in seasonal_data:
            seasonal_data[season_key] = {
                'count': 0,
                'hours': 0,
                'rating': 0,
                'deepSleep': 0,
                'cycles': 0
            }
        
        seasonal_data[season_key]['count'] += 1
        seasonal_data[season_key]['hours'] += record['hours']
        seasonal_data[season_key]['rating'] += record['rating']
        seasonal_data[season_key]['deepSleep'] += record['deepSleep']
        seasonal_data[season_key]['cycles'] += record['cycles']
    
    # Calculate averages
    for season_key in seasonal_data:
        count = seasonal_data[season_key]['count']
        seasonal_data[season_key]['hours'] /= count
        seasonal_data[season_key]['rating'] /= count
        seasonal_data[season_key]['deepSleep'] /= count
        seasonal_data[season_key]['cycles'] /= count
    
    return seasonal_data

def process_events(events):
    """Process and categorize sleep events"""
    event_categories = {
        'sleep_stages': ['DEEP_START', 'DEEP_END', 'REM_START', 'REM_END', 'LIGHT_START', 'LIGHT_END'],
        'awake': ['AWAKE_START', 'AWAKE_END'],
        'alarm': ['ALARM_EARLIEST', 'ALARM_LATEST', 'ALARM_STARTED', 'ALARM_SNOOZE'],
        'other': ['DEVICE', 'TRACKING_STOPPED_BY_USER', 'LUX', 'DHA']
    }
    
    categorized_events = {category: [] for category in event_categories}
    
    for event in events:
        event_parts = event.split('-')
        event_type = event_parts[0]
        for category, types in event_categories.items():
            if event_type in types:
                categorized_events[category].append(event)
                break
    
    return categorized_events

def format_event_time(event):
    """Format event time if available"""
    try:
        parts = event.split('-')
        if len(parts) > 1:
            timestamp = int(parts[1])
            return datetime.fromtimestamp(timestamp/1000).strftime('%H:%M:%S')
    except:
        pass
    return None

def get_event_statistics(sleep_records):
    """Calculate statistics about sleep events"""
    stats = {
        'total_records': len(sleep_records),
        'records_with_events': 0,
        'event_counts': {
            'sleep_stages': 0,
            'awake': 0,
            'alarm': 0,
            'other': 0
        },
        'average_events_per_record': 0
    }
    
    total_events = 0
    for record in sleep_records:
        events = record.get('events', [])
        if events:
            stats['records_with_events'] += 1
            total_events += len(events)
            categorized = process_events(events)
            for category, events_list in categorized.items():
                stats['event_counts'][category] += len(events_list)
    
    stats['average_events_per_record'] = total_events / stats['total_records'] if stats['total_records'] > 0 else 0
    return stats

def generate_html(sleep_records, monthly_data, yearly_data, seasonal_data):
    """Generate HTML with Tailwind CSS for sleep data visualization"""
    # Calculate event statistics
    event_stats = get_event_statistics(sleep_records)
    
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Sleep Data Visualization - Complete History</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    </head>
    <body class="bg-gray-100 min-h-screen">
        <div class="container mx-auto px-4 py-8">
            <h1 class="text-3xl font-bold text-gray-800 mb-8">Sleep Data - Complete History</h1>
            
            <!-- Summary Cards -->
            <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                <div class="bg-white rounded-lg shadow-lg p-6">
                    <h3 class="text-sm font-medium text-gray-500">Total Records</h3>
                    <p class="text-2xl font-bold text-gray-900">{len(sleep_records)}</p>
                </div>
                <div class="bg-white rounded-lg shadow-lg p-6">
                    <h3 class="text-sm font-medium text-gray-500">Average Sleep Duration</h3>
                    <p class="text-2xl font-bold text-gray-900">{sum(r['hours'] for r in sleep_records)/len(sleep_records):.1f}h</p>
                </div>
                <div class="bg-white rounded-lg shadow-lg p-6">
                    <h3 class="text-sm font-medium text-gray-500">Average Quality</h3>
                    <p class="text-2xl font-bold text-gray-900">{sum(r['rating'] for r in sleep_records)/len(sleep_records):.1f}/5</p>
                </div>
                <div class="bg-white rounded-lg shadow-lg p-6">
                    <h3 class="text-sm font-medium text-gray-500">Average Deep Sleep</h3>
                    <p class="text-2xl font-bold text-gray-900">{sum(r['deepSleep']*100 for r in sleep_records)/len(sleep_records):.1f}%</p>
                </div>
            </div>
            
            <!-- Event Statistics -->
            <div class="bg-white rounded-lg shadow-lg p-6 mb-8">
                <h2 class="text-xl font-semibold text-gray-700 mb-4">Sleep Event Statistics</h2>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div class="bg-gray-50 rounded-lg p-4">
                        <h3 class="text-lg font-medium text-gray-700 mb-2">Event Distribution</h3>
                        <canvas id="eventDistributionChart" class="w-full h-48"></canvas>
                    </div>
                    <div class="bg-gray-50 rounded-lg p-4">
                        <h3 class="text-lg font-medium text-gray-700 mb-2">Event Statistics</h3>
                        <div class="space-y-2">
                            <p class="text-sm text-gray-600">Records with Events: {event_stats['records_with_events']}</p>
                            <p class="text-sm text-gray-600">Average Events per Record: {event_stats['average_events_per_record']:.1f}</p>
                            <p class="text-sm text-gray-600">Sleep Stage Events: {event_stats['event_counts']['sleep_stages']}</p>
                            <p class="text-sm text-gray-600">Awake Events: {event_stats['event_counts']['awake']}</p>
                            <p class="text-sm text-gray-600">Alarm Events: {event_stats['event_counts']['alarm']}</p>
                            <p class="text-sm text-gray-600">Other Events: {event_stats['event_counts']['other']}</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Yearly Trends -->
            <div class="bg-white rounded-lg shadow-lg p-6 mb-8">
                <h2 class="text-xl font-semibold text-gray-700 mb-4">Yearly Sleep Trends</h2>
                <canvas id="yearlyTrendsChart" class="w-full h-64"></canvas>
            </div>
            
            <!-- Seasonal Trends -->
            <div class="bg-white rounded-lg shadow-lg p-6 mb-8">
                <h2 class="text-xl font-semibold text-gray-700 mb-4">Seasonal Sleep Patterns</h2>
                <canvas id="seasonalTrendsChart" class="w-full h-64"></canvas>
            </div>
            
            <!-- Monthly Trends -->
            <div class="bg-white rounded-lg shadow-lg p-6 mb-8">
                <h2 class="text-xl font-semibold text-gray-700 mb-4">Monthly Sleep Duration Trend</h2>
                <canvas id="monthlyDurationChart" class="w-full h-64"></canvas>
            </div>
            
            <!-- Sleep Quality Trend -->
            <div class="bg-white rounded-lg shadow-lg p-6 mb-8">
                <h2 class="text-xl font-semibold text-gray-700 mb-4">Monthly Sleep Quality Trend</h2>
                <canvas id="monthlyQualityChart" class="w-full h-64"></canvas>
            </div>
            
            <!-- Deep Sleep Trend -->
            <div class="bg-white rounded-lg shadow-lg p-6 mb-8">
                <h2 class="text-xl font-semibold text-gray-700 mb-4">Monthly Deep Sleep Trend</h2>
                <canvas id="monthlyDeepSleepChart" class="w-full h-64"></canvas>
            </div>
            
            <!-- Yearly Summary Table -->
            <div class="bg-white rounded-lg shadow-lg p-6 mb-8">
                <h2 class="text-xl font-semibold text-gray-700 mb-4">Yearly Summary</h2>
                <div class="overflow-x-auto">
                    <table class="min-w-full divide-y divide-gray-200">
                        <thead class="bg-gray-50">
                            <tr>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Year</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Records</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Avg Duration</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Avg Quality</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Avg Deep Sleep</th>
                            </tr>
                        </thead>
                        <tbody class="bg-white divide-y divide-gray-200">
                            {''.join([f"""
                            <tr class="hover:bg-gray-50">
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{year_key}</td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{data['count']}</td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{data['hours']:.1f}h</td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{data['rating']:.1f}/5</td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{data['deepSleep']*100:.1f}%</td>
                            </tr>
                            """ for year_key, data in yearly_data.items()])}
                        </tbody>
                    </table>
                </div>
            </div>
            
            <!-- Recent Records -->
            <div class="bg-white rounded-lg shadow-lg p-6">
                <h2 class="text-xl font-semibold text-gray-700 mb-4">Recent Records (Last 30 Days)</h2>
                <div class="overflow-x-auto">
                    <table class="min-w-full divide-y divide-gray-200">
                        <thead class="bg-gray-50">
                            <tr>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Duration</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Quality</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Deep Sleep</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cycles</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Events</th>
                            </tr>
                        </thead>
                        <tbody class="bg-white divide-y divide-gray-200">
                            {''.join([f"""
                            <tr class="hover:bg-gray-50">
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                    {datetime.fromtimestamp(record['fromTime']/1000).strftime('%Y-%m-%d %H:%M')}
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                    {record['hours']:.1f} hours
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                    {record['rating']:.1f}/5
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                    {record['deepSleep']*100:.1f}%
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                    {record['cycles']}
                                </td>
                                <td class="px-6 py-4 text-sm text-gray-900">
                                    <div class="space-y-1">
                                        {''.join([f"""
                                        <div class="text-xs">
                                            <span class="font-medium">{event.split('-')[0]}</span>
                                            {f'<span class="text-gray-500">({format_event_time(event)})</span>' if format_event_time(event) else ''}
                                        </div>
                                        """ for event in record.get('events', [])])}
                                    </div>
                                </td>
                            </tr>
                            """ for record in sleep_records[:30]])}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Detailed Sleep Analysis -->
            <div class="bg-white rounded-lg shadow-lg p-6 mt-8">
                <h2 class="text-xl font-semibold text-gray-700 mb-4">Detailed Sleep Analysis</h2>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <!-- Sleep Duration Distribution -->
                    <div class="bg-gray-50 rounded-lg p-4">
                        <h3 class="text-lg font-medium text-gray-700 mb-2">Sleep Duration Distribution</h3>
                        <canvas id="sleepDurationDistribution" class="w-full h-48"></canvas>
                    </div>
                    
                    <!-- Sleep Quality Distribution -->
                    <div class="bg-gray-50 rounded-lg p-4">
                        <h3 class="text-lg font-medium text-gray-700 mb-2">Sleep Quality Distribution</h3>
                        <canvas id="sleepQualityDistribution" class="w-full h-48"></canvas>
                    </div>
                    
                    <!-- Deep Sleep Distribution -->
                    <div class="bg-gray-50 rounded-lg p-4">
                        <h3 class="text-lg font-medium text-gray-700 mb-2">Deep Sleep Distribution</h3>
                        <canvas id="deepSleepDistribution" class="w-full h-48"></canvas>
                    </div>
                    
                    <!-- Sleep Cycles Distribution -->
                    <div class="bg-gray-50 rounded-lg p-4">
                        <h3 class="text-lg font-medium text-gray-700 mb-2">Sleep Cycles Distribution</h3>
                        <canvas id="sleepCyclesDistribution" class="w-full h-48"></canvas>
                    </div>
                </div>
            </div>
        </div>

        <script>
            // Yearly Trends Chart
            new Chart(document.getElementById('yearlyTrendsChart'), {{
                type: 'line',
                data: {{
                    labels: {[f"'{year_key}'" for year_key in yearly_data.keys()]},
                    datasets: [
                        {{
                            label: 'Sleep Duration (hours)',
                            data: {[f"{data['hours']:.1f}" for data in yearly_data.values()]},
                            borderColor: 'rgb(59, 130, 246)',
                            tension: 0.1,
                            yAxisID: 'y1'
                        }},
                        {{
                            label: 'Sleep Quality',
                            data: {[f"{data['rating']:.1f}" for data in yearly_data.values()]},
                            borderColor: 'rgb(16, 185, 129)',
                            tension: 0.1,
                            yAxisID: 'y2'
                        }},
                        {{
                            label: 'Deep Sleep %',
                            data: {[f"{data['deepSleep']*100:.1f}" for data in yearly_data.values()]},
                            borderColor: 'rgb(139, 92, 246)',
                            tension: 0.1,
                            yAxisID: 'y3'
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    scales: {{
                        y1: {{
                            type: 'linear',
                            position: 'left',
                            title: {{
                                display: true,
                                text: 'Hours'
                            }}
                        }},
                        y2: {{
                            type: 'linear',
                            position: 'right',
                            title: {{
                                display: true,
                                text: 'Quality (0-5)'
                            }},
                            max: 5,
                            min: 0
                        }},
                        y3: {{
                            type: 'linear',
                            position: 'right',
                            title: {{
                                display: true,
                                text: 'Deep Sleep %'
                            }},
                            max: 100,
                            min: 0
                        }}
                    }}
                }}
            }});

            // Seasonal Trends Chart
            new Chart(document.getElementById('seasonalTrendsChart'), {{
                type: 'line',
                data: {{
                    labels: {[f"'{season_key}'" for season_key in seasonal_data.keys()]},
                    datasets: [
                        {{
                            label: 'Sleep Duration (hours)',
                            data: {[f"{data['hours']:.1f}" for data in seasonal_data.values()]},
                            borderColor: 'rgb(59, 130, 246)',
                            tension: 0.1,
                            yAxisID: 'y1'
                        }},
                        {{
                            label: 'Sleep Quality',
                            data: {[f"{data['rating']:.1f}" for data in seasonal_data.values()]},
                            borderColor: 'rgb(16, 185, 129)',
                            tension: 0.1,
                            yAxisID: 'y2'
                        }},
                        {{
                            label: 'Deep Sleep %',
                            data: {[f"{data['deepSleep']*100:.1f}" for data in seasonal_data.values()]},
                            borderColor: 'rgb(139, 92, 246)',
                            tension: 0.1,
                            yAxisID: 'y3'
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    scales: {{
                        y1: {{
                            type: 'linear',
                            position: 'left',
                            title: {{
                                display: true,
                                text: 'Hours'
                            }}
                        }},
                        y2: {{
                            type: 'linear',
                            position: 'right',
                            title: {{
                                display: true,
                                text: 'Quality (0-5)'
                            }},
                            max: 5,
                            min: 0
                        }},
                        y3: {{
                            type: 'linear',
                            position: 'right',
                            title: {{
                                display: true,
                                text: 'Deep Sleep %'
                            }},
                            max: 100,
                            min: 0
                        }}
                    }}
                }}
            }});

            // Monthly Duration Chart
            new Chart(document.getElementById('monthlyDurationChart'), {{
                type: 'line',
                data: {{
                    labels: {[f"'{month_key}'" for month_key in monthly_data.keys()]},
                    datasets: [{{
                        label: 'Average Sleep Duration (hours)',
                        data: {[f"{data['hours']:.1f}" for data in monthly_data.values()]},
                        borderColor: 'rgb(59, 130, 246)',
                        tension: 0.1
                    }}]
                }},
                options: {{
                    responsive: true,
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            title: {{
                                display: true,
                                text: 'Hours'
                            }}
                        }}
                    }}
                }}
            }});

            // Monthly Quality Chart
            new Chart(document.getElementById('monthlyQualityChart'), {{
                type: 'line',
                data: {{
                    labels: {[f"'{month_key}'" for month_key in monthly_data.keys()]},
                    datasets: [{{
                        label: 'Average Sleep Quality',
                        data: {[f"{data['rating']:.1f}" for data in monthly_data.values()]},
                        borderColor: 'rgb(16, 185, 129)',
                        tension: 0.1
                    }}]
                }},
                options: {{
                    responsive: true,
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            max: 5,
                            title: {{
                                display: true,
                                text: 'Rating (0-5)'
                            }}
                        }}
                    }}
                }}
            }});

            // Monthly Deep Sleep Chart
            new Chart(document.getElementById('monthlyDeepSleepChart'), {{
                type: 'line',
                data: {{
                    labels: {[f"'{month_key}'" for month_key in monthly_data.keys()]},
                    datasets: [{{
                        label: 'Average Deep Sleep',
                        data: {[f"{data['deepSleep']*100:.1f}" for data in monthly_data.values()]},
                        borderColor: 'rgb(139, 92, 246)',
                        tension: 0.1
                    }}]
                }},
                options: {{
                    responsive: true,
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            max: 100,
                            title: {{
                                display: true,
                                text: 'Percentage'
                            }}
                        }}
                    }}
                }}
            }});

            // Sleep Duration Distribution Chart
            new Chart(document.getElementById('sleepDurationDistribution'), {{
                type: 'bar',
                data: {{
                    labels: ['< 6h', '6-7h', '7-8h', '8-9h', '> 9h'],
                    datasets: [{{
                        label: 'Number of Records',
                        data: [
                            {len([r for r in sleep_records if r['hours'] < 6])},
                            {len([r for r in sleep_records if 6 <= r['hours'] < 7])},
                            {len([r for r in sleep_records if 7 <= r['hours'] < 8])},
                            {len([r for r in sleep_records if 8 <= r['hours'] < 9])},
                            {len([r for r in sleep_records if r['hours'] >= 9])}
                        ],
                        backgroundColor: 'rgb(59, 130, 246)'
                    }}]
                }},
                options: {{
                    responsive: true,
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            title: {{
                                display: true,
                                text: 'Number of Records'
                            }}
                        }}
                    }}
                }}
            }});

            // Sleep Quality Distribution Chart
            new Chart(document.getElementById('sleepQualityDistribution'), {{
                type: 'bar',
                data: {{
                    labels: ['1', '2', '3', '4', '5'],
                    datasets: [{{
                        label: 'Number of Records',
                        data: [
                            {len([r for r in sleep_records if r['rating'] == 1])},
                            {len([r for r in sleep_records if r['rating'] == 2])},
                            {len([r for r in sleep_records if r['rating'] == 3])},
                            {len([r for r in sleep_records if r['rating'] == 4])},
                            {len([r for r in sleep_records if r['rating'] == 5])}
                        ],
                        backgroundColor: 'rgb(16, 185, 129)'
                    }}]
                }},
                options: {{
                    responsive: true,
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            title: {{
                                display: true,
                                text: 'Number of Records'
                            }}
                        }}
                    }}
                }}
            }});

            // Deep Sleep Distribution Chart
            new Chart(document.getElementById('deepSleepDistribution'), {{
                type: 'bar',
                data: {{
                    labels: ['< 10%', '10-20%', '20-30%', '30-40%', '> 40%'],
                    datasets: [{{
                        label: 'Number of Records',
                        data: [
                            {len([r for r in sleep_records if r['deepSleep'] < 0.1])},
                            {len([r for r in sleep_records if 0.1 <= r['deepSleep'] < 0.2])},
                            {len([r for r in sleep_records if 0.2 <= r['deepSleep'] < 0.3])},
                            {len([r for r in sleep_records if 0.3 <= r['deepSleep'] < 0.4])},
                            {len([r for r in sleep_records if r['deepSleep'] >= 0.4])}
                        ],
                        backgroundColor: 'rgb(139, 92, 246)'
                    }}]
                }},
                options: {{
                    responsive: true,
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            title: {{
                                display: true,
                                text: 'Number of Records'
                            }}
                        }}
                    }}
                }}
            }});

            // Sleep Cycles Distribution Chart
            new Chart(document.getElementById('sleepCyclesDistribution'), {{
                type: 'bar',
                data: {{
                    labels: ['< 3', '3-4', '4-5', '5-6', '> 6'],
                    datasets: [{{
                        label: 'Number of Records',
                        data: [
                            {len([r for r in sleep_records if r['cycles'] < 3])},
                            {len([r for r in sleep_records if 3 <= r['cycles'] < 4])},
                            {len([r for r in sleep_records if 4 <= r['cycles'] < 5])},
                            {len([r for r in sleep_records if 5 <= r['cycles'] < 6])},
                            {len([r for r in sleep_records if r['cycles'] >= 6])}
                        ],
                        backgroundColor: 'rgb(245, 158, 11)'
                    }}]
                }},
                options: {{
                    responsive: true,
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            title: {{
                                display: true,
                                text: 'Number of Records'
                            }}
                        }}
                    }}
                }}
            }});

            // Event Distribution Chart
            new Chart(document.getElementById('eventDistributionChart'), {{
                type: 'doughnut',
                data: {{
                    labels: ['Sleep Stages', 'Awake', 'Alarm', 'Other'],
                    datasets: [{{
                        data: [
                            {event_stats['event_counts']['sleep_stages']},
                            {event_stats['event_counts']['awake']},
                            {event_stats['event_counts']['alarm']},
                            {event_stats['event_counts']['other']}
                        ],
                        backgroundColor: [
                            'rgb(59, 130, 246)',
                            'rgb(16, 185, 129)',
                            'rgb(245, 158, 11)',
                            'rgb(139, 92, 246)'
                        ]
                    }}]
                }},
                options: {{
                    responsive: true,
                    plugins: {{
                        legend: {{
                            position: 'right'
                        }}
                    }}
                }}
            }});
        </script>
    </body>
    </html>
    """
    return html

def main():
    try:
        # Load sleep data
        sleep_data = load_sleep_data('sleep_data_2016_to_2025.json')
        
        # Get all data
        all_data = get_all_years_data(sleep_data)
        
        # Calculate monthly, yearly, and seasonal averages
        monthly_data = get_monthly_averages(all_data)
        yearly_data = get_yearly_averages(all_data)
        seasonal_data = get_seasonal_averages(all_data)
        
        # Generate HTML
        html_content = generate_html(all_data, monthly_data, yearly_data, seasonal_data)
        
        # Save HTML file
        with open('sleep_visualization.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info("Visualization generated successfully")
        
    except Exception as e:
        logger.error(f"Error generating visualization: {str(e)}")
        raise

if __name__ == "__main__":
    main() 