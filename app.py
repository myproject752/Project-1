import os
import re
import json
import requests
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# HTML Template as a string (unchanged from your original)
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Food Product Health Scanner</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css">
    <style>
        /* Main Styles */
        body {
            background-color: #f8f9fa;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        .container {
            max-width: 1000px;
        }

        header h1 {
            color: #2c3e50;
            font-weight: 700;
        }

        /* Scanner Styles */
        #scanner-container {
            position: relative;
            width: 100%;
            height: 300px;
            overflow: hidden;
            border-radius: 8px;
            background-color: #000;
        }

        #interactive.viewport {
            position: relative;
            width: 100%;
            height: 100%;
        }

        #interactive.viewport > canvas, video {
            width: 100%;
            height: 100%;
            position: absolute;
            top: 0;
            left: 0;
        }

        #interactive.viewport canvas.drawingBuffer {
            width: 100%;
            height: 100%;
            position: absolute;
            top: 0;
            left: 0;
        }

        /* Product Info Styles */
        .product-image {
            max-height: 200px;
            object-fit: contain;
            border-radius: 4px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }

        #health-badge.badge-success {
            background-color: #28a745;
            color: white;
        }

        #health-badge.badge-warning {
            background-color: #ffc107;
            color: #212529;
        }

        #health-badge.badge-danger {
            background-color: #dc3545;
            color: white;
        }

        /* List Styles */
        .list-group-item {
            padding: 0.5rem 1rem;
            border: none;
            background-color: transparent;
        }

        .list-group-item-success {
            color: #155724;
            background-color: #d4edda;
        }

        .list-group-item-warning {
            color: #856404;
            background-color: #fff3cd;
        }

        .list-group-item-danger {
            color: #721c24;
            background-color: #f8d7da;
        }

        /* Nutrition Info Styles */
        .nutrition-item {
            padding: 8px;
            border-radius: 4px;
            margin-bottom: 8px;
            background-color: #f1f1f1;
        }

        .nutrition-item .value {
            font-weight: bold;
        }

        .nutrition-item.high {
            background-color: #f8d7da;
        }

        .nutrition-item.medium {
            background-color: #fff3cd;
        }

        .nutrition-item.low {
            background-color: #d4edda;
        }

        /* Responsive Adjustments */
        @media (max-width: 768px) {
            #scanner-container {
                height: 240px;
            }
            
            .col-md-4, .col-md-8 {
                padding: 0 15px;
            }
        }
    </style>
    <script src="https://cdn.jsdelivr.net/npm/quagga@0.12.1/dist/quagga.min.js"></script>
</head>
<body>
    <div class="container">
        <header class="text-center my-4">
            <h1>Food Product Health Scanner</h1>
            <p class="lead">Scan a barcode or enter a barcode number to get health information about food products</p>
        </header>

        <div class="row justify-content-center">
            <div class="col-md-8">
                <div class="card mb-4">
                    <div class="card-header">
                        <ul class="nav nav-tabs card-header-tabs" id="scanTabs" role="tablist">
                            <li class="nav-item" role="presentation">
                                <button class="nav-link active" id="camera-tab" data-bs-toggle="tab" data-bs-target="#camera" type="button" role="tab" aria-controls="camera" aria-selected="true">Scan Barcode</button>
                            </li>
                            <li class="nav-item" role="presentation">
                                <button class="nav-link" id="manual-tab" data-bs-toggle="tab" data-bs-target="#manual" type="button" role="tab" aria-controls="manual" aria-selected="false">Enter Barcode</button>
                            </li>
                        </ul>
                    </div>
                    <div class="card-body">
                        <div class="tab-content" id="scanTabsContent">
                            <div class="tab-pane fade show active" id="camera" role="tabpanel" aria-labelledby="camera-tab">
                                <div id="scanner-container" class="mb-3">
                                    <div id="interactive" class="viewport"></div>
                                </div>
                                <div class="d-grid gap-2">
                                    <button id="start-scanner" class="btn btn-primary">Start Scanner</button>
                                    <button id="stop-scanner" class="btn btn-secondary" disabled>Stop Scanner</button>
                                </div>
                            </div>
                            <div class="tab-pane fade" id="manual" role="tabpanel" aria-labelledby="manual-tab">
                                <form id="barcode-form">
                                    <div class="mb-3">
                                        <label for="barcode-input" class="form-label">Barcode Number</label>
                                        <input type="text" class="form-control" id="barcode-input" placeholder="Enter barcode number (e.g., 3017620422003)">
                                    </div>
                                    <div class="d-grid gap-2">
                                        <button type="submit" class="btn btn-primary">Search Product</button>
                                    </div>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>

                <div id="loading" class="text-center d-none">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p>Fetching product information...</p>
                </div>

                <div id="error-message" class="alert alert-danger d-none" role="alert"></div>

                <div id="product-info" class="card d-none">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h2 id="product-name" class="h5 mb-0"></h2>
                        <span id="health-badge" class="badge"></span>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-4 text-center mb-3">
                                <img id="product-image" src="" alt="Product Image" class="img-fluid product-image mb-2">
                                <p id="product-brand" class="text-muted"></p>
                                <div id="product-details" class="mb-3"></div>
                            </div>
                            <div class="col-md-8">
                                <div class="mb-3">
                                    <h3 class="h6">Health Assessment</h3>
                                    <ul id="health-reasons" class="list-group list-group-flush"></ul>
                                </div>
                                
                                <div class="mb-3">
                                    <h3 class="h6">Age Recommendations</h3>
                                    <div class="row">
                                        <div class="col-md-6">
                                            <h4 class="h6 text-success">Suitable for:</h4>
                                            <ul id="suitable-ages" class="list-group list-group-flush"></ul>
                                        </div>
                                        <div class="col-md-6">
                                            <h4 class="h6 text-danger">Not suitable for:</h4>
                                            <ul id="not-suitable-ages" class="list-group list-group-flush"></ul>
                                        </div>
                                    </div>
                                    <div class="mt-3">
                                        <h4 class="h6">Reasons:</h4>
                                        <ul id="age-reasons" class="list-group list-group-flush"></ul>
                                    </div>
                                </div>
                                
                                <div class="mb-3">
                                    <h3 class="h6">Ingredients</h3>
                                    <p id="ingredients-text"></p>
                                </div>
                                
                                <div class="mb-3">
                                    <h3 class="h6">Nutrition Information (per 100g)</h3>
                                    <div class="row" id="nutrition-info">
                                        <!-- Nutrition info will be inserted here -->
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            // DOM Elements
            const startScannerBtn = document.getElementById('start-scanner');
            const stopScannerBtn = document.getElementById('stop-scanner');
            const barcodeForm = document.getElementById('barcode-form');
            const barcodeInput = document.getElementById('barcode-input');
            const loadingElement = document.getElementById('loading');
            const errorMessage = document.getElementById('error-message');
            const productInfo = document.getElementById('product-info');
            
            // Scanner state
            let scannerInitialized = false;
            let scannerRunning = false;
            
            // Event Listeners
            startScannerBtn.addEventListener('click', startScanner);
            stopScannerBtn.addEventListener('click', stopScanner);
            barcodeForm.addEventListener('submit', handleManualSubmit);
            
            // Tab switching event listeners
            document.getElementById('camera-tab').addEventListener('click', function() {
                if (scannerInitialized && !scannerRunning) {
                    startScannerBtn.disabled = false;
                    stopScannerBtn.disabled = true;
                }
            });
            
            // Initialize scanner when camera tab is shown
            const cameraTabs = document.querySelectorAll('button[data-bs-toggle="tab"]');
            cameraTabs.forEach(tab => {
                tab.addEventListener('shown.bs.tab', function(event) {
                    if (event.target.id === 'camera-tab' && !scannerInitialized) {
                        initScanner();
                    }
                });
            });
            
            // Functions
            function initScanner() {
                Quagga.init({
                    inputStream: {
                        name: "Live",
                        type: "LiveStream",
                        target: document.querySelector('#interactive'),
                        constraints: {
                            width: 640,
                            height: 480,
                            facingMode: "environment"
                        },
                    },
                    locator: {
                        patchSize: "medium",
                        halfSample: true
                    },
                    numOfWorkers: navigator.hardwareConcurrency || 4,
                    decoder: {
                        readers: [
                            "ean_reader",
                            "ean_8_reader",
                            "upc_reader",
                            "upc_e_reader"
                        ]
                    },
                    locate: true
                }, function(err) {
                    if (err) {
                        console.error("Error initializing scanner:", err);
                        showError("Could not initialize barcode scanner. Please ensure you've granted camera permissions or use manual entry.");
                        return;
                    }
                    
                    scannerInitialized = true;
                    startScannerBtn.disabled = false;
                    
                    Quagga.onDetected(handleBarcodeDetection);
                });
            }
            
            function startScanner() {
                if (!scannerInitialized) {
                    initScanner();
                    return;
                }
                
                Quagga.start();
                scannerRunning = true;
                startScannerBtn.disabled = true;
                stopScannerBtn.disabled = false;
            }
            
            function stopScanner() {
                if (scannerRunning) {
                    Quagga.stop();
                    scannerRunning = false;
                    startScannerBtn.disabled = false;
                    stopScannerBtn.disabled = true;
                }
            }
            
            function handleBarcodeDetection(result) {
                if (result && result.codeResult) {
                    const barcode = result.codeResult.code;
                    stopScanner();
                    
                    // Clean barcode - remove any non-numeric characters
                    const cleanedBarcode = barcode.replace(/[^0-9]/g, '');
                    
                    // Validate barcode
                    if (!cleanedBarcode || cleanedBarcode.length < 8) {
                        showError('Invalid barcode detected. Please try scanning again with better lighting or enter the barcode manually.');
                        return;
                    }
                    
                    searchProduct(cleanedBarcode);
                }
            }
            
            function handleManualSubmit(event) {
                event.preventDefault();
                const barcode = barcodeInput.value.trim();
                
                if (!barcode) {
                    showError("Please enter a barcode number");
                    return;
                }
                
                searchProduct(barcode);
            }
            
            function searchProduct(barcode) {
                // Show loading state
                showLoading();
                hideError();
                
                // Clean barcode input - remove any non-numeric characters
                const cleanedBarcode = barcode.replace(/[^0-9]/g, '');
                
                // Validate barcode
                if (!cleanedBarcode || cleanedBarcode.length < 8) {
                    hideLoading();
                    showError('Invalid barcode format. Please provide a numeric barcode with at least 8 digits.<br><br>Try removing any spaces or special characters.');
                    return;
                }
                
                // Make API request
                fetch('/search', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: `barcode=${encodeURIComponent(cleanedBarcode)}`
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`Server responded with status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    hideLoading();
                    
                    if (data.error) {
                        // Show error message with suggestions
                        let errorMessage = data.error;
                        if (data.error.includes('Product not found')) {
                            errorMessage += '<br><br>Suggestions:<ul>' +
                                '<li>Try scanning the barcode again or enter it manually</li>' +
                                '<li>Make sure the barcode is clear and complete</li>' +
                                '<li>This product may not be in the Open Food Facts database</li>' +
                                '<li>Try a different product</li>' +
                                '</ul>';
                        }
                        showError(errorMessage);
                        return;
                    }
                    
                    displayProductInfo(data);
                })
                .catch(error => {
                    hideLoading();
                    const errorHTML = 'An error occurred while fetching product information.<br><br>' +
                        'Possible reasons:<ul>' +
                        '<li>Network connection issues</li>' +
                        '<li>Server is temporarily unavailable</li>' +
                        '<li>The barcode format may be incorrect</li>' +
                        '</ul>' +
                        'Please try again later or with a different product.';
                    showError(errorHTML);
                    console.error("Error fetching product:", error);
                });
            }
            
            function displayProductInfo(product) {
                // Hide error message if visible
                hideError();
                
                // Set product name and brand
                document.getElementById('product-name').textContent = product.name || 'Unknown Product';
                document.getElementById('product-brand').textContent = product.brands || '';
                
                // Set product image
                const productImage = document.getElementById('product-image');
                if (product.image_url) {
                    productImage.src = product.image_url;
                    productImage.alt = product.name;
                } else {
                    productImage.src = 'https://via.placeholder.com/200x200?text=No+Image';
                    productImage.alt = 'No image available';
                }
                
                // Add additional product details if available
                let productDetails = '';
                if (product.categories) {
                    productDetails += `<strong>Category:</strong> ${product.categories}<br>`;
                }
                if (product.countries) {
                    productDetails += `<strong>Countries:</strong> ${product.countries}<br>`;
                }
                if (product.origin) {
                    productDetails += `<strong>Origin:</strong> ${product.origin}<br>`;
                }
                if (product.labels) {
                    productDetails += `<strong>Labels:</strong> ${product.labels}<br>`;
                }
                if (product.india_message) {
                    productDetails += `<div class="alert alert-info mt-2">${product.india_message}</div>`;
                }
                
                // Add product details to the page if element exists
                const productDetailsElement = document.getElementById('product-details');
                if (productDetailsElement) {
                    productDetailsElement.innerHTML = productDetails;
                }
                
                // Set health badge
                const healthBadge = document.getElementById('health-badge');
                if (product.health_assessment) {
                    if (product.health_assessment.overall_rating) {
                        // New format with overall_rating
                        if (product.health_assessment.overall_rating === 'Good') {
                            healthBadge.textContent = 'Good';
                            healthBadge.className = 'badge badge-success';
                        } else if (product.health_assessment.overall_rating === 'Average') {
                            healthBadge.textContent = 'Average';
                            healthBadge.className = 'badge badge-warning';
                        } else {
                            healthBadge.textContent = 'Poor';
                            healthBadge.className = 'badge badge-danger';
                        }
                    } else {
                        // Old format with is_healthy
                        healthBadge.textContent = product.health_assessment.is_healthy ? 'Healthy' : 'Not Healthy';
                        healthBadge.className = 'badge ' + (product.health_assessment.is_healthy ? 'badge-success' : 'badge-danger');
                    }
                    
                    // Set health reasons
                    const healthReasonsList = document.getElementById('health-reasons');
                    healthReasonsList.innerHTML = '';
                    
                    // Handle both new and old format
                    if (product.health_assessment.positives) {
                        // New format with positives/negatives
                        product.health_assessment.positives.forEach(point => {
                            const li = document.createElement('li');
                            li.className = 'list-group-item list-group-item-success';
                            li.textContent = point;
                            healthReasonsList.appendChild(li);
                        });
                        
                        product.health_assessment.negatives.forEach(point => {
                            const li = document.createElement('li');
                            li.className = 'list-group-item list-group-item-danger';
                            li.textContent = point;
                            healthReasonsList.appendChild(li);
                        });
                    } else if (product.health_assessment.reasons) {
                        // Old format with reasons array
                        product.health_assessment.reasons.forEach(reason => {
                            const li = document.createElement('li');
                            li.className = 'list-group-item';
                            li.textContent = reason;
                            healthReasonsList.appendChild(li);
                        });
                    }
                }
                
                // Set age recommendations
                const suitableAgesList = document.getElementById('suitable-ages');
                const notSuitableAgesList = document.getElementById('not-suitable-ages');
                
                suitableAgesList.innerHTML = '';
                notSuitableAgesList.innerHTML = '';
                
                if (product.age_recommendations) {
                    // Handle both new and old format
                    const suitableAges = product.age_recommendations.suitable_for || 
                                        product.age_recommendations.suitable || [];
                    
                    const notSuitableAges = product.age_recommendations.not_suitable_for || 
                                           product.age_recommendations.not_suitable || [];
                    
                    suitableAges.forEach(age => {
                        const li = document.createElement('li');
                        li.className = 'list-group-item list-group-item-success';
                        li.textContent = age;
                        suitableAgesList.appendChild(li);
                    });
                    
                    notSuitableAges.forEach(age => {
                        const li = document.createElement('li');
                        li.className = 'list-group-item list-group-item-danger';
                        li.textContent = age;
                        notSuitableAgesList.appendChild(li);
                    });
                    
                    // Add reasons if available in new format
                    if (product.age_recommendations.reasons) {
                        const reasonsElement = document.getElementById('age-reasons');
                        if (reasonsElement) {
                            reasonsElement.innerHTML = '';
                            product.age_recommendations.reasons.forEach(reason => {
                                const li = document.createElement('li');
                                li.className = 'list-group-item';
                                li.textContent = reason;
                                reasonsElement.appendChild(li);
                            });
                        }
                    }
                }
                
                // Set ingredients
                document.getElementById('ingredients-text').textContent = product.ingredients || 'Ingredients information not available';
                
                // Set nutrition information
                const nutritionInfo = document.getElementById('nutrition-info');
                nutritionInfo.innerHTML = '';
                
                const nutriments = product.nutriments;
                if (nutriments && Object.keys(nutriments).length > 0) {
                    // Display key nutrients
                    const keyNutrients = [
                        { name: 'Energy', key: 'energy-kcal_100g', unit: 'kcal', high: 400, medium: 200 },
                        { name: 'Fat', key: 'fat_100g', unit: 'g', high: 17.5, medium: 3 },
                        { name: 'Saturated Fat', key: 'saturated-fat_100g', unit: 'g', high: 5, medium: 1.5 },
                        { name: 'Sugars', key: 'sugars_100g', unit: 'g', high: 22.5, medium: 5 },
                        { name: 'Salt', key: 'salt_100g', unit: 'g', high: 1.5, medium: 0.3 },
                        { name: 'Fiber', key: 'fiber_100g', unit: 'g', high: 6, medium: 3 },
                        { name: 'Proteins', key: 'proteins_100g', unit: 'g', high: 20, medium: 10 }
                    ];
                    
                    keyNutrients.forEach(nutrient => {
                        if (nutriments[nutrient.key] !== undefined) {
                            const value = parseFloat(nutriments[nutrient.key]);
                            let levelClass = 'medium';
                            
                            // For nutrients where high is good (fiber, protein)
                            if (nutrient.name === 'Fiber' || nutrient.name === 'Proteins') {
                                levelClass = value >= nutrient.high ? 'low' : (value >= nutrient.medium ? 'medium' : 'high');
                            } else {
                                levelClass = value >= nutrient.high ? 'high' : (value >= nutrient.medium ? 'medium' : 'low');
                            }
                            
                            const col = document.createElement('div');
                            col.className = 'col-6 col-md-4';
                            col.innerHTML = `
                                <div class="nutrition-item ${levelClass}">
                                    <div class="name">${nutrient.name}</div>
                                    <div class="value">${value} ${nutrient.unit}</div>
                                </div>
                            `;
                            nutritionInfo.appendChild(col);
                        }
                    });
                } else {
                    const noInfo = document.createElement('div');
                    noInfo.className = 'col-12';
                    noInfo.innerHTML = '<p>Nutrition information not available</p>';
                    nutritionInfo.appendChild(noInfo);
                }
                
                // Show product info section
                productInfo.classList.remove('d-none');
                
                // Scroll to product info
                productInfo.scrollIntoView({ behavior: 'smooth' });
            }
            
            function showLoading() {
                loadingElement.classList.remove('d-none');
                errorMessage.classList.add('d-none');
                productInfo.classList.add('d-none');
            }
            
            function hideLoading() {
                loadingElement.classList.add('d-none');
            }
            
            function showError(message) {
                errorMessage.innerHTML = message;
                errorMessage.classList.remove('d-none');
                productInfo.classList.add('d-none');
                
                // Scroll to error message for better visibility
                errorMessage.scrollIntoView({ behavior: 'smooth' });
            }
                
            function hideError() {
                errorMessage.classList.add('d-none');
            }
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/search', methods=['POST'])
def search_product():
    barcode = request.form.get('barcode', '')
    
    # Clean barcode - remove any non-numeric characters
    cleaned_barcode = re.sub(r'[^0-9]', '', barcode)
    
    # Validate barcode
    if not cleaned_barcode or len(cleaned_barcode) < 8:
        return jsonify({
            'error': 'Invalid barcode format. Please provide a numeric barcode with at least 8 digits.'
        })
    
    # Try different Open Food Facts API endpoints
    api_endpoints = [
        f"https://world.openfoodfacts.org/api/v0/product/{cleaned_barcode}.json",
        f"https://us.openfoodfacts.org/api/v0/product/{cleaned_barcode}.json",
        f"https://uk.openfoodfacts.org/api/v0/product/{cleaned_barcode}.json",
        f"https://in.openfoodfacts.org/api/v0/product/{cleaned_barcode}.json"
    ]
    
    product_data = None
    endpoint_used = None
    
    for endpoint in api_endpoints:
        try:
            response = requests.get(endpoint, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 1 and data.get('product'):
                    product_data = data.get('product')
                    endpoint_used = endpoint
                    break
        except (requests.RequestException, json.JSONDecodeError) as e:
            continue
    
    if not product_data:
        return jsonify({
            'error': 'Product not found. The barcode may not be in the Open Food Facts database.'
        })
    
    # Extract product information
    product_info = {
        'name': product_data.get('product_name', 'Unknown Product'),
        'brands': product_data.get('brands', ''),
        'image_url': product_data.get('image_url'),
        'categories': product_data.get('categories', ''),
        'countries': product_data.get('countries', ''),
        'origin': product_data.get('origins', 'Unknown'),
        'labels': product_data.get('labels', ''),
        'ingredients': product_data.get('ingredients_text', ''),
        'allergens': product_data.get('allergens_tags', []),
        'additives_tags': product_data.get('additives_tags', []),
        'nutriments': product_data.get('nutriments', {}),
        'nutrition_grade': product_data.get('nutrition_grade_fr', ''),
        'nova_group': product_data.get('nova_group', ''),
        'india_message': 'For Indian users: Please verify product details with local regulations.' if 'in.openfoodfacts.org' in endpoint_used else ''
    }
    
    # Assess health
    product_info['health_assessment'] = assess_health(product_info)
    
    # Get age recommendations
    product_info['age_recommendations'] = get_age_recommendations(product_info)
    
    return jsonify(product_info)

def assess_health(product_info):
    """Assess the health aspects of the product"""
    assessment = {
        'overall_rating': 'Average',  # Default rating
        'positives': [],
        'negatives': []
    }
    
    # Check nutrition grade
    nutrition_grade = product_info.get('nutrition_grade', '')
    if nutrition_grade:
        if nutrition_grade in ['a', 'b']:
            assessment['positives'].append(f"Good nutrition grade ({nutrition_grade.upper()})")
            assessment['overall_rating'] = 'Good'
        elif nutrition_grade == 'c':
            assessment['positives'].append(f"Average nutrition grade ({nutrition_grade.upper()})")
        else:  # d or e
            assessment['negatives'].append(f"Poor nutrition grade ({nutrition_grade.upper()})")
            assessment['overall_rating'] = 'Poor'
    
    # Check sugar content
    nutriments = product_info.get('nutriments', {})
    try:
        sugar_100g = float(nutriments.get('sugars_100g', 0) or 0)
        if sugar_100g > 22.5:
            assessment['negatives'].append(f"High sugar content ({sugar_100g}g per 100g)")
            assessment['overall_rating'] = 'Poor'
        elif sugar_100g > 5:
            assessment['negatives'].append(f"Medium sugar content ({sugar_100g}g per 100g)")
        else:
            assessment['positives'].append(f"Low sugar content ({sugar_100g}g per 100g)")
    except (ValueError, TypeError):
        pass
    
    # Check fat content
    try:
        fat_100g = float(nutriments.get('fat_100g', 0) or 0)
        if fat_100g > 17.5:
            assessment['negatives'].append(f"High fat content ({fat_100g}g per 100g)")
            assessment['overall_rating'] = 'Poor'
        elif fat_100g > 3:
            assessment['negatives'].append(f"Medium fat content ({fat_100g}g per 100g)")
        else:
            assessment['positives'].append(f"Low fat content ({fat_100g}g per 100g)")
    except (ValueError, TypeError):
        pass
    
    # Check additives
    additives = product_info.get('additives_tags', [])
    if len(additives) > 5:
        assessment['negatives'].append(f"Contains many additives ({len(additives)})")
        assessment['overall_rating'] = 'Poor'
    elif len(additives) > 0:
        assessment['negatives'].append(f"Contains some additives ({len(additives)})")
    else:
        assessment['positives'].append("No additives")
    
    # Check for palm oil
    ingredients = product_info.get('ingredients', '')
    if isinstance(ingredients, str) and 'palm oil' in ingredients.lower():
        assessment['negatives'].append("Contains palm oil")
    
    # Check NOVA group (food processing classification)
    try:
        nova_group = int(product_info.get('nova_group', 0))
        if nova_group == 4:
            assessment['negatives'].append("Ultra-processed food (NOVA group 4)")
            assessment['overall_rating'] = 'Poor'
        elif nova_group == 3:
            assessment['negatives'].append("Processed food (NOVA group 3)")
        elif nova_group in [1, 2]:
            assessment['positives'].append(f"Minimally processed food (NOVA group {nova_group})")
            if assessment['overall_rating'] != 'Poor':
                assessment['overall_rating'] = 'Good'
    except (ValueError, TypeError):
        pass
    
    # If no specific positives or negatives were found
    if not assessment['positives'] and not assessment['negatives']:
        assessment['positives'].append("Limited information available for detailed assessment")
    
    return assessment

def get_age_recommendations(product_info):
    """Determine suitable age groups for the product"""
    recommendations = {
        'suitable_for': [],
        'not_suitable_for': [],
        'reasons': []
    }
    
    all_age_groups = [
        'Infants (0-12 months)', 
        'Young children (1-3 years)', 
        'Children (4-8 years)', 
        'Older children (9-13 years)', 
        'Teenagers (14-18 years)', 
        'Adults (19-64 years)', 
        'Elderly (65+ years)', 
        'Pregnant women'
    ]
    
    # Check for allergens (common allergens make product unsuitable for infants and young children)
    allergens = product_info.get('allergens', [])
    common_allergens = ['nuts', 'peanuts', 'milk', 'eggs', 'fish', 'shellfish', 'soy', 'wheat', 'gluten', 'celery', 'mustard', 'sesame', 'sulphites', 'lupin', 'molluscs']
    
    detected_allergens = []
    for allergen in allergens:
        for common in common_allergens:
            if common in allergen.lower():
                detected_allergens.append(common)
    
    if detected_allergens:
        recommendations['not_suitable_for'].append('Infants (0-12 months)')
        recommendations['not_suitable_for'].append('people with allergies to: ' + ', '.join(allergens))
        recommendations['reasons'].append(f"Contains allergens: {', '.join(allergens)}")
        if len(detected_allergens) > 1:
            recommendations['not_suitable_for'].append('Young children (1-3 years)')
    
    # Check sugar content (high sugar is not good for children)
    nutriments = product_info.get('nutriments', {})
    try:
        sugar_100g = float(nutriments.get('sugars_100g', 0) or 0)
        if sugar_100g > 10:
            recommendations['not_suitable_for'].extend(['Children (4-8 years)', 'Infants (0-12 months)', 'Young children (1-3 years)', 'people with diabetes'])
            recommendations['reasons'].append(f"High sugar content ({sugar_100g}g per 100g)")
        elif sugar_100g > 5:
            recommendations['not_suitable_for'].extend(['Infants (0-12 months)'])
    except (ValueError, TypeError):
        # Sugar content not available or not a valid number
        pass
    
    # Check salt content (high salt is not good for elderly and infants)
    try:
        salt_100g = float(nutriments.get('salt_100g', 0) or 0)
        if salt_100g > 1.5:
            recommendations['not_suitable_for'].extend(['Elderly (65+ years)', 'Infants (0-12 months)', 'people with hypertension'])
            recommendations['reasons'].append(f"High salt content ({salt_100g}g per 100g)")
        elif salt_100g > 0.8:
            recommendations['not_suitable_for'].extend(['Infants (0-12 months)'])
    except (ValueError, TypeError):
        # Salt content not available or not a valid number
        pass
    
    # Check additives (many additives not good for children and pregnant women)
    additives = product_info.get('additives_tags', [])
    if len(additives) > 3:
        recommendations['not_suitable_for'].extend(['Pregnant women', 'Infants (0-12 months)', 'Young children (1-3 years)'])
        recommendations['reasons'].append("Contains many additives")
    
    # Check NOVA group (highly processed foods not good for certain groups)
    try:
        nova_group = int(product_info.get('nova_group', 0))
        if nova_group == 4:  # Ultra-processed food
            recommendations['not_suitable_for'].extend(['Infants (0-12 months)', 'Young children (1-3 years)', 'Pregnant women'])
            recommendations['reasons'].append(f"Highly processed food (NOVA group {nova_group})")
    except (ValueError, TypeError):
        # Nova group not available or not a valid number
        pass
    
    # Remove duplicates
    recommendations['not_suitable_for'] = list(set(recommendations['not_suitable_for']))
    
    # Default recommendations if no specific issues found
    if not recommendations['not_suitable_for']:
        recommendations['suitable_for'].append('all age groups')
        recommendations['reasons'].append("No specific concerns identified")
    else:
        # Add suitable age groups that aren't in the not_suitable list
        age_groups = ['Teenagers (14-18 years)', 'Adults (19-64 years)']
        for group in age_groups:
            if group not in recommendations['not_suitable_for']:
                recommendations['suitable_for'].append(group)
    
    # If no suitable groups were found, add adults as default
    if not recommendations['suitable_for']:
        recommendations['suitable_for'].append('Adults (19-64 years)')
    
    return recommendations

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)  # Debug mode OFF for production