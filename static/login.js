$(document).ready(function() {

	// State varaibles
	var crossword = null;
	var currentDirectionHorizontal = null; // is later set to either true or false


	// Focus the username_input field
	$('#username_input').focus();

	// For the username_input field, make the enter key trigger a click on the 'Next' button
	$('#username_input').on('keydown', function(event) {
		if (event.keyCode == 13) {
			$('#next').click();
		}
	});


	// Function to update the crossword and other relevant information to reflect whether the 
	// next move is in the vertical or horizontal direction
	var updateCrosswordDisplayDirection = function() {

		// Ensure the direction is either true or false
		if (currentDirectionHorizontal !== true && currentDirectionHorizontal !== false) {
			return;
		}

		// Update the text indicating the direction
		var directionText;
		if (currentDirectionHorizontal === true) {
			directionText = 'Move Direction: Horizontal';
		} 
		else {
			directionText = 'Move Direction: Vertical';
		}
		$('#direction').html(directionText);


		// Change every other row/column (except the starting cell) to be a different color (by adding a CSS class)
		// Whether it changes the rows or columns depends on the current direction
		var crosswordContent = crossword['crosswordContent'];
		var startX = crossword['startX'];
		var startY = crossword['startY'];
		var width = crossword['width'];
		for (var row = 0; row < crosswordContent.length/width; row++) {
			for (var col = 0; col < width; col++) {

				// Skip the starting cell
				if (row == startY && col == startX)
					continue;

				 // Get the cell
				var cell = $('#td' + (row*width + col) );

				// Select the row or column depending on the currentDirection
				if ((row % 2 == 0 && currentDirectionHorizontal) || (col % 2 == 0 && !currentDirectionHorizontal))
					cell.addClass('highlightedCell');
				else
					cell.removeClass('highlightedCell');
			}
		}

	};



	// When the 'Next' button is clicked, perform a get request to get the crossword
	$('#next').click(function() {
		var username = $('#username_input').val();

		$.get('./crossword/'+username, function (data) {
			// Only process the response if there isn't a crossword in place already
			if ($('#cross_table').html().length !== 0) {
				return;
			};

			// If the data is a string, then it is an error message
			// Return
			if (typeof data == 'string') {
				$('#flash').html(data + '<br /><br />');
				return;
			}

			
			// Clear all flash (error messages)
			$('#flash').html("");


			// Get the crossword information
			crossword = data; // Save the crossword
			var crosswordContent = crossword['crosswordContent'];
			var startX = crossword['startX'];
			var startY = crossword['startY'];
			var width = crossword['width'];
			currentDirectionHorizontal = crossword['startHorizontal'];

			// Put the username into a hidden form input
			$('#username_hidden_input').val(username);

			// Replace the username div with the username text
			$('#username_div').html('<strong>Username: </strong>' + username);

			// Create crossword using HTML Table
			var crosswordDiv = $('#crossword');
			var crossTable = $('#cross_table');
			var tbody = crossTable.append('<tbody />').children('tbody');
			for (var y = 0; y < crosswordContent.length/width; y++) {
				// Add row to crossTable
				tbody.append('<tr />').children('tr:last');
				for (var x = 0; x < width; x++) {
					var crosswordLetter = crosswordContent[y*width + x];
					// If the letter is the start position, mark it with a different class
					// Also add an id to the cell, "td#", where # is the index (row major)
					if (x == startX && y == startY) {
						tbody.append("<td id=td" + (y*width + x) + " class='startLetter'>" + crosswordLetter + "</td>");
					}
                	else {
                		tbody.append("<td id=td" + (y*width + x) + ">" + crosswordLetter + "</td>");
                	}
                };
            };

            // Show the direction box and display the correct direction text
            $('#direction').css('visibility', 'visible');
            updateCrosswordDisplayDirection();

			// Show the trace_form and focus on the trace_input
			$('#trace_form').css('visibility', 'visible');
			$('#trace_input').focus();

		}); // End of $.get callback

	}); // End of $('#next').click callback



	// For the trace_input, make it only accept arrow key presses as input.
	// The arrow key presses are translated to text (Left -> 'l', Up -> 'u', Right -> 'r', Down -> 'd')
	$('#trace_input').on('keydown', function(event) {
		// Save the previous input value
		var traceText = $('#trace_input').val();

		// Translate the arrow key to a letter
		var keyCode = event.keyCode;
		var directionLetter = ''; // l, u, r, d
	    // Left key
	    if (keyCode == 37) {
	    	directionLetter = 'l';
	    }
	    // Up key
	    else if (keyCode == 38) {
	    	directionLetter = 'u';
	    }
	    // Right key
	    else if (keyCode == 39) {
	    	directionLetter = 'r';
	    }
	    // Down key
	    else if (keyCode == 40) {
	    	directionLetter = 'd';
	    }
	    // Backspace key (delete a keypress)
	    else if (keyCode == 8) {
	    	// Delete a letter in the traceText
	    	var prevTraceText = traceText;
	    	traceText = traceText.substring(0, traceText.length-1);
	    	$('#trace_input').val(traceText);

		   	// Switch the direction and update the direction text if the letter was deleted
		   	if (prevTraceText.length !== traceText.length) {
			    currentDirectionHorizontal = !currentDirectionHorizontal;
		        updateCrosswordDisplayDirection();
		    }

    	    // Cancel event bubbling
		    event.preventDefault();
	        return;
	    }
	    // Enter or Tab key (pass the event on as normal)
	    else if (keyCode == 13 || keyCode == 9) {
	    	return;
	    }
	    // Else do nothing (and cancel event bubbling)
	    else {
		    // Cancel event bubbling
		    event.preventDefault();
	    	return;
	    }


	    // Add the letter to the input only if the letter matches the direction
	    if (currentDirectionHorizontal) {
	    	if (directionLetter === 'u' || directionLetter === 'd') {
			    // Cancel event bubbling
			    event.preventDefault();
	    		return;
	    	}
	    }
	    else {
	    	if (directionLetter === 'l' || directionLetter === 'r') {
			    // Cancel event bubbling
			    event.preventDefault();
	    		return;
	    	}
	    }
	    $('#trace_input').val(traceText + directionLetter);


	   	// Switch the direction and update the direction text
	    currentDirectionHorizontal = !currentDirectionHorizontal;
        updateCrosswordDisplayDirection();

	    // Cancel event bubbling
	    event.preventDefault();

	    //console.log(event);
	});

}); // End of $(document).ready callback