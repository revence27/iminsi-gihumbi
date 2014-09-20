	
				
				//START FILTERING LOCATIONS
				var locations = [];
				

				$.getJSON( "/locs" , function( result ){
				
						var provinces = _.map(_.indexBy(result, 'province_id'), function(obj){return obj});
					
						for ( var i=0; i<provinces.length; i++ ){
							province = provinces[i]
							document.getElementById('provchoose').options.length= provinces.length;
							document.getElementById('provchoose').options[i] = new Option(province.province_name, province.province_id);
							}

				
						locations = result;

						// IS There a province selected, then apply
						sel_prov = getQueryParameter ( "province" );
						if (sel_prov != '' ){
								 changeDistrict(sel_prov);
								 prv_index = fetch_index_from_option_value(document.getElementById('provchoose').options, sel_prov);
								 document.getElementById('provchoose').options[prv_index].selected = true;
								 
								     }

						// IS There a district selected, then apply
						sel_dist = getQueryParameter ( "district" );
						if (sel_prov != '' && sel_dist != '') {
								changeLocation(sel_dist);
								dist_index = fetch_index_from_option_value(document.getElementById('distchoose').options, sel_dist);
							 	document.getElementById('distchoose').options[dist_index].selected = true;
									}

						// IS There a location selected, then apply
						sel_loc = getQueryParameter ( "location" );
						if (sel_loc != '' && sel_dist != '') { 
									changeLocation(sel_dist);
								loc_index = fetch_index_from_option_value(document.getElementById('locchoose').options, sel_loc);
							 	document.getElementById('locchoose').options[loc_index].selected = true;
								}
						
						
	    					});
					
				function fetch_index_from_option_value(options, value){
											for(i=0;i<options.length;i++) 
											{ 
											if(options[i].value == value) break; 
											
											 }
											
											return i
											}

				function changeDistrict(value){

					var districts = _.map(_.indexBy(locations, 'district_id'), function(obj){ return obj });

					var selected_districts = _.filter(districts, function(item) {  return item.province_id == value;  });
			
					for ( var i=0; i<selected_districts.length; i++ ){
							district = selected_districts[i]
							document.getElementById('distchoose').options.length = selected_districts.length;
							document.getElementById('distchoose').options[i] = new Option(district.district_name, district.district_id);
								}


					}

				function changeLocation(value){

					var selected_locations = _.filter(locations, function(item) {  return item.district_id == value; });
			
					for ( var i=0; i<selected_locations.length; i++ ){
								hc = selected_locations[i]
								document.getElementById('locchoose').options.length = selected_locations.length;
								document.getElementById('locchoose').options[i] = new Option(hc.name, hc.id);
								}

					}
				
				function PassCheck(filter_form){
					
						// FIX CASES YOU CAN FORGET TO DISABLE SOME FILTERS AND THEY ARE EMPTY ... 
						if(filter_form.provchoose.value == ""){
											filter_form.provchoose.disabled = true;
											}
						else if(filter_form.distchoose.value == ""){
											filter_form.distchoose.disabled = true;
											}
						else if(filter_form.locchoose.value==""){
											filter_form.locchoose.disabled = true;
										}

						filter_form.submit();

					}

				function getQueryParameter ( parameterName ) {

						  var queryString = window.top.location.search.substring(1);
						  var parameterName = parameterName + "=";
						  if ( queryString.length > 0 ) {
						    begin = queryString.indexOf ( parameterName );
						    if ( begin != -1 ) {
						      begin += parameterName.length;
						      end = queryString.indexOf ( "&" , begin );
							if ( end == -1 ) {
							end = queryString.length
						      }
						      return unescape ( queryString.substring ( begin, end ) );
						    }
						  }
						  return "";

						} 


				// END FILTERING
				