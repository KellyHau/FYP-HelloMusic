const { Factory, Renderer, Stave, Voice, Formatter } = Vex.Flow;

// Initialize music state
let measures = [[]];
let measureWidths = []; 
let currentMeasureIndex = 0;
let selectedNote = null;
let synth = null;
let isPlaying = false;
let audioInitialized = false;
let draggedDuration = null;
let staffLineHighlight = null;
let staffSpaceHighlight = null;

// Duration mappings
const DURATIONS = {
  "w": { ticks: 4096, beats: 4, time: "1n" },    // Whole note
  "h": { ticks: 2048, beats: 2, time: "2n" },    // Half note
  "q": { ticks: 1024, beats: 1, time: "4n" },    // Quarter note
  "8": { ticks: 512, beats: 0.5, time: "8n" },   // Eighth note
  "16": { ticks: 256, beats: 0.25, time: "16n" }, // Sixteenth note
  "wr": { ticks: 4096, beats: 4, time: "1n" },   // Whole rest
  "hr": { ticks: 2048, beats: 2, time: "2n" },   // Half rest
  "qr": { ticks: 1024, beats: 1, time: "4n" },   // Quarter rest
  "8r": { ticks: 512, beats: 0.5, time: "8n" },  // Eighth rest
  "16r": { ticks: 256, beats: 0.25, time: "16n" } // Sixteenth rest
};

// Note frequency mappings
const NOTE_FREQUENCIES = {
  c: 261.63,
  d: 293.66,
  e: 329.63,
  f: 349.23,
  g: 392.0,
  a: 440.0,
  b: 493.88,
};

// History management
const history = {
  undoStack: [],
  redoStack: [],
  
  pushState() {
      // Convert measures to a serializable format
      const serializableMeasures = measures.map(measure => 
          measure.map(note => ({
              keys: note.keys,
              duration: note.duration,
              accidental: note.modifiers.find(m => m instanceof Vex.Flow.Accidental)?.type,
              articulation: note.modifiers.find(m => m instanceof Vex.Flow.Articulation)?.type,
              tied: note.tied,
              tieStart: note.tieStart
          }))
      );
      
      this.undoStack.push(JSON.stringify(serializableMeasures));
      this.redoStack = [];
      if (this.undoStack.length > 50) this.undoStack.shift();
  },
  
  undo() {
      if (this.undoStack.length > 0) {
          const currentState = this.serializeMeasures(measures);
          this.redoStack.push(currentState);
          const previousState = JSON.parse(this.undoStack.pop());
          measures = this.deserializeMeasures(previousState);
          initializeStaves();
      }
  },
  
  redo() {
      if (this.redoStack.length > 0) {
          const currentState = this.serializeMeasures(measures);
          this.undoStack.push(currentState);
          const nextState = JSON.parse(this.redoStack.pop());
          measures = this.deserializeMeasures(nextState);
          initializeStaves();
      }
  },
  
  serializeMeasures(measures) {
      const serializableMeasures = measures.map(measure => 
          measure.map(note => ({
              keys: note.keys,
              duration: note.duration,
              accidental: note.modifiers.find(m => m instanceof Vex.Flow.Accidental)?.type,
              articulation: note.modifiers.find(m => m instanceof Vex.Flow.Articulation)?.type,
              tied: note.tied,
              tieStart: note.tieStart
          }))
      );
      return JSON.stringify(serializableMeasures);
  },
  
  deserializeMeasures(serializedMeasures) {
      return serializedMeasures.map(measure =>
          measure.map(noteData => {
              const note = new Vex.Flow.StaveNote({
                  keys: noteData.keys,
                  duration: noteData.duration
              });
              
              if (noteData.accidental) {
                  note.addAccidental(0, new Vex.Flow.Accidental(noteData.accidental));
              }
              
              if (noteData.articulation) {
                  note.addArticulation(0, new Vex.Flow.Articulation(noteData.articulation));
              }
              
              note.tied = noteData.tied;
              note.tieStart = noteData.tieStart;
              
              return note;
          })
      );
  }
};

// Constants for layout
const MEASURE_WIDTH = 350;
const MEASURE_MIN_WIDTH = 300;
const MEASURES_PER_ROW = 4;
const ROW_HEIGHT = 210;
const STAFF_TOP_OFFSET = 100;
const STAFF_LINE_SPACING = 5;

// Helper function to get CSRF token
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
          const cookie = cookies[i].trim();
          if (cookie.substring(0, name.length + 1) === (name + '=')) {
              cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
              break;
          }
      }
  }
  return cookieValue;
}

function saveSheetData() {
  const sheetId = document.getElementById('sheet-editor').dataset.sheetId;
  const timeSignature = document.getElementById('time-select').value;
  const keySignature = document.getElementById('key-signature').value;
  const clefType = document.getElementById('clef-select').value;

  // Prepare measures data
  const measuresData = measures.map((measure, measureIndex) => {
      const notes = [];
      const rests = [];

      measure.forEach(note => {
          if (note.duration.includes('r')) {
              rests.push({
                  duration: note.duration.replace('r', '')
              });
          } else {
              notes.push({
                  pitch: note.keys[0],
                  duration: note.duration,
                  tie: note.tieStart ? 'start' : (note.tied ? 'end' : ''),
                  accidental: note.modifiers.find(m => m instanceof Vex.Flow.Accidental)?.type || '',
                  duration_value: DURATIONS[note.duration]?.beats || 1.0,
                  dynamics: '',
                  articulation: note.modifiers.find(m => m instanceof Vex.Flow.Articulation)?.type || ''
              });
          }
      });

      return {
          measure_number: measureIndex + 1,
          time_signature: timeSignature,
          notes: notes,
          rests: rests
      };
  });

  // Prepare data for sending
  const data = {
      timeSignature: timeSignature,
      keySignature: keySignature,
      clefType: clefType,
      measures: measuresData
  };

  // Send data to server
  fetch(`/api/save_sheet/${sheetId}/`, {
      method: 'POST',
      headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken')
      },
      body: JSON.stringify(data)
  })
  .then(response => response.json())
  .then(data => {
      if (data.status === 'success') {
          console.log('Sheet saved successfully');
      } else {
          console.error('Error saving sheet:', data.message);
      }
  })
  .catch(error => console.error('Error saving sheet:', error));
}

// Add auto-save triggers
let saveTimeout;
function triggerAutoSave() {
    clearTimeout(saveTimeout);
    saveTimeout = setTimeout(saveSheetData, 1000); // Save after 2 seconds of no changes
}

// Initialize Tone.js
async function initAudio() {
  try {
    await Tone.start();
    console.log('Audio is ready');
    
    if (!synth) {
        synth = new Tone.Synth().toDestination();
    }
    audioInitialized = true;
    return true;
  } catch (error) {
      console.error('Failed to initialize audio:', error);
      return false;
  }
}

// Initialize VexFlow for each measure
function initializeStaves() {
  const staffContainer = document.getElementById('staff-container');
  staffContainer.innerHTML = '';
  
  const measuresPerRow = 4;
  const totalRows = Math.ceil(measures.length / measuresPerRow);
  
  // Reset measure widths array
  measureWidths = [];
  
  for (let row = 0; row < totalRows; row++) {
      const div = document.createElement('div');
      div.className = 'staff-row';
      div.id = `staff-row-${row}`;
      staffContainer.appendChild(div);
      
      // Calculate widths for measures in this row
      const startMeasureIndex = row * measuresPerRow;
      const rowMeasures = measures.slice(startMeasureIndex, startMeasureIndex + measuresPerRow);
      
      // Calculate required widths
      const rowWidths = rowMeasures.map((measure, i) => {
          let width = MEASURE_MIN_WIDTH;
          
          if (measure && measure.length > 0) {
              // Add extra width for longer measures
              width = Math.max(width, MEASURE_MIN_WIDTH + (measure.length * 25));
          }
          
          // Add extra space for clef and signatures if first measure
          if (i === 0) {
              width += 60;
          }
          
          // Store the calculated width
          measureWidths[startMeasureIndex + i] = width;
          return width;
      });
      
      const totalRowWidth = rowWidths.reduce((sum, width) => sum + width, 0);
      const renderer = new Vex.Flow.Renderer(div, Vex.Flow.Renderer.Backends.SVG);
      renderer.resize(totalRowWidth, 150);
      const context = renderer.getContext();
      
      let currentX = 0;
      for (let i = 0; i < measuresPerRow && (startMeasureIndex + i) < measures.length; i++) {
          const measureIndex = startMeasureIndex + i;
          const width = rowWidths[i];
          
          const stave = new Vex.Flow.Stave(currentX, 40, width);
          
          if (i === 0) {
              const clef = document.getElementById('clef-select').value;
              stave.addClef(clef);
              const keySignature = document.getElementById('key-signature').value;
              stave.addKeySignature(keySignature);
              if (row === 0) {
                  const timeSignature = document.getElementById('time-select').value;
                  stave.addTimeSignature(timeSignature);
              }
          }

          stave.setEndBarType(measureIndex === measures.length - 1 ? 
              Vex.Flow.Barline.type.END : Vex.Flow.Barline.type.SINGLE);
          
          stave.setContext(context).draw();
          
          if (measureIndex < measures.length) {
              drawMeasure(measures[measureIndex], stave, context);
          }
          
          currentX += width;
      }
  }
}

// Initialize preview system
function initializePreviewSystem() {
  createHighlightElements();

  // Add drag event listeners to draggable notes
  document.querySelectorAll('.draggable-note').forEach(note => {
      note.addEventListener('dragstart', handleDragStart);
      note.addEventListener('dragend', handleDragEnd);
  });

  // Add drag event listeners to staff container
  const staffContainer = document.querySelector('.staff-scroll-container');
  
  // Remove any existing listeners
  staffContainer.removeEventListener('dragover', handleDragOver);
  staffContainer.removeEventListener('dragleave', handleDragLeave);
  staffContainer.removeEventListener('drop', handleDrop);
  
  // Add fresh listeners
  staffContainer.addEventListener('dragover', handleDragOver);
  staffContainer.addEventListener('dragleave', handleDragLeave);
  staffContainer.addEventListener('drop', handleDrop);
}

function getTimeSignature() {
  const timeSig = document.getElementById("time-select").value;
  const [num, den] = timeSig.split("/").map(Number);
  return { num, den };
}

// Add getCurrentBeats function if not already present
function getCurrentBeats(measureIndex) {
  if (!measures[measureIndex]) return 0;
  
  return measures[measureIndex].reduce((sum, note) => {
      const duration = note.duration.replace('r', ''); // Remove 'r' from rest durations
      return sum + (DURATIONS[duration]?.beats || 0);
  }, 0);
}

//    function getAccidentalSymbol(type) {
//     const accidentalMap = {
//         'sharp': '#',
//         'flat': 'b',
//         'natural': 'n'
//     };
//     return accidentalMap[type] || '#';
//   } 

//    function getArticulationSymbol(type) {
//     const articulationMap = {
//         'staccato': 'a.',
//         'legato': 'a-',
//         'accent': 'a>'
//     };
//     return articulationMap[type] || 'a.';
//   } 

// Add getCurrentTicks function
function getCurrentTicks(measureIndex) {
  if (!measures[measureIndex]) return 0;
  
  return measures[measureIndex].reduce((sum, note) => {
      const duration = note.duration.split("r")[0];
      return sum + (DURATIONS[duration]?.ticks || 0);
  }, 0);
}

// Helper function to get appropriate duration for beats
function getDurationForBeats(beats) {
  if (beats === 4) return 'w';
  if (beats === 2) return 'h';
  if (beats === 1) return 'q';
  if (beats === 0.5) return '8';
  if (beats === 0.25) return '16';
  return 'q'; // default
}

function getMeasureIndexFromPosition(x, scrollLeft, currentRowIndex) {
  const measuresPerRow = 4;
  const rowStartIndex = currentRowIndex * measuresPerRow;
  let currentX = 0;
  
  // Find which measure we're in by accumulating widths
  for (let i = 0; i < measuresPerRow; i++) {
      const measureIndex = rowStartIndex + i;
      if (measureIndex >= measureWidths.length) break;
      
      const measureWidth = measureWidths[measureIndex];
      if (x >= currentX && x < currentX + measureWidth) {
          return measureIndex;
      }
      currentX += measureWidth;
  }
  
  // If we're past all measures in this row, return the last valid measure
  return Math.min(rowStartIndex + measuresPerRow - 1, measures.length - 1);
}

function calculateRowAndMeasure(x, y, scrollLeft, scrollTop) {
  const rowHeight = 210;
  const rowIndex = Math.floor((y + scrollTop) / rowHeight);
  const rowRelativeX = x; // x is already relative to the container
  
  return {
      rowIndex,
      measureIndex: getMeasureIndexFromPosition(rowRelativeX, scrollLeft, rowIndex)
  };
}

// Function to calculate row and measure from coordinates
function calculatePositionFromCoords(x, y, scrollLeft, scrollTop) {
  const rowIndex = Math.floor((y + scrollTop) / ROW_HEIGHT);
  const measureIndex = rowIndex * MEASURES_PER_ROW + Math.floor((x + scrollLeft) / MEASURE_WIDTH);
  return { rowIndex, measureIndex };
}

// Function to get note name based on staff position
function getNoteNameFromPosition(lineIndex, clef) {
  // Define positions for both clefs using the same visual position mapping
  const notePositions = {
      10: { treble: "c/4", bass: "e/2", type: "line" },    // Bottom ledger line
      9: { treble: "d/4", bass: "f/2", type: "space" },    // Space between ledger lines
      8: { treble: "e/4", bass: "g/2", type: "line" },     // Bottom line of staff
      7: { treble: "f/4", bass: "a/2", type: "space" },    // First space
      6: { treble: "g/4", bass: "b/2", type: "line" },     // Second line
      5: { treble: "a/4", bass: "c/3", type: "space" },    // Second space
      4: { treble: "b/4", bass: "d/3", type: "line" },     // Middle line
      3: { treble: "c/5", bass: "e/3", type: "space" },    // Third space
      2: { treble: "d/5", bass: "f/3", type: "line" },     // Fourth line
      1: { treble: "e/5", bass: "g/3", type: "space" },    // Fourth space
      0: { treble: "f/5", bass: "a/3", type: "line" },     // Top line
      "-1": { treble: "g/5", bass: "b/3", type: "space" }, // Space above staff
      "-2": { treble: "a/5", bass: "c/4", type: "line" }   // Top ledger line
  };

  const position = notePositions[lineIndex];
  if (!position) return null;

  return {
      note: clef === "treble" ? position.treble : position.bass,
      type: position.type
  };
}

function fillWithRests(voice, measureNotes, totalTicks, stave, context) {
  if (!measureNotes || measureNotes.length === 0) {
      // For empty measures, add a whole rest
      const rest = new Vex.Flow.StaveNote({
          keys: ["b/4"],
          duration: "wr"
      });
      voice.addTickable(rest);
  } else {
      let currentTicks = 0;
      
      // First pass: add all existing notes
      for (let note of measureNotes) {
          voice.addTickable(note);
          const duration = note.duration.replace('r', '');
          currentTicks += DURATIONS[duration]?.ticks || 0;
      }
      
      // Only add rests if there's space and we need to fill the measure
      if (currentTicks < totalTicks) {
          let remainingTicks = totalTicks - currentTicks;
          
          while (remainingTicks >= 256) { // 256 ticks = 16th note
              let restDuration;
              if (remainingTicks >= 4096) restDuration = "wr";
              else if (remainingTicks >= 2048) restDuration = "hr";
              else if (remainingTicks >= 1024) restDuration = "qr";
              else if (remainingTicks >= 512) restDuration = "8r";
              else restDuration = "16r";
              
              const restTicks = DURATIONS[restDuration.replace('r', '')].ticks;
              if (restTicks <= remainingTicks) {
                  const rest = new Vex.Flow.StaveNote({
                      keys: ["b/4"],
                      duration: restDuration
                  });
                  voice.addTickable(rest);
                  remainingTicks -= restTicks;
              } else {
                  break;
              }
          }
      }
  }

  const formatter = new Vex.Flow.Formatter();
  try {
      const availableWidth = stave.getWidth() - (stave.getNoteStartX() - stave.getX()) - 10;
      formatter.joinVoices([voice]);
      formatter.format([voice], availableWidth);
      voice.draw(context, stave);
  } catch (error) {
      console.error('Formatting error:', error);
  }
}

// Helper function to create note object
function createNote(duration, lineIndex, clef) {
  // Get position info
  const positionInfo = getNoteNameFromPosition(lineIndex, clef);
  
  if (!positionInfo) {
      return null;
  }

  // Create the note with the correct pitch but keep the original line position
  const note = new Vex.Flow.StaveNote({
      keys: [positionInfo.note],
      duration: duration,
      auto_stem: true,
      clef: clef  // Explicitly set the clef
  });
  
  return note;
}

function addNote(duration, x, y, measureIndex) {
  const rowHeight = 210;
  const rowIndex = Math.floor(y / rowHeight);
  const staffTop = 80 + (rowHeight * rowIndex);
  const staffLineSpacing = 5;
  const relativeY = y - staffTop;
  const lineIndex = Math.round(relativeY / staffLineSpacing);
  
  if (lineIndex >= -2 && lineIndex <= 10) {
      const clef = document.getElementById('clef-select').value;
      const note = createNote(duration, lineIndex, clef);
      
      if (note) {
          const { num, den } = getTimeSignature();
          const maxBeatsPerMeasure = num;
          
          // Calculate current beats in the measure
          const currentBeats = getCurrentBeats(measureIndex);
          const newNoteBeats = DURATIONS[duration]?.beats || 0;
          
          // Ensure measures array exists up to this index
          while (measures.length <= measureIndex) {
              measures.push([]);
          }
          
          // Check if note fits in current measure
          if (currentBeats + newNoteBeats <= maxBeatsPerMeasure) {
              measures[measureIndex].push(note);
          } else {
              // Look for the next measure that has space
              let nextMeasureIndex = measureIndex + 1;
              while (measures.length <= nextMeasureIndex) {
                  measures.push([]);
              }
              
              const nextMeasureBeats = getCurrentBeats(nextMeasureIndex);
              if (nextMeasureBeats + newNoteBeats <= maxBeatsPerMeasure) {
                  measures[nextMeasureIndex].push(note);
              } else {
                  // If no space in next measure, create a new one
                  measures.push([note]);
              }
          }
          
          history.pushState();
          initializeStaves();
      }
  }
  triggerAutoSave();
}

function drawMeasure(measureNotes, stave, context) {
  const { num, den } = getTimeSignature();
  const totalTicks = (num / den) * 4096;
  
  const voice = new Vex.Flow.Voice({
      num_beats: num,
      beat_value: den,
      resolution: Vex.Flow.RESOLUTION
  }).setMode(Vex.Flow.Voice.Mode.SOFT);  // Add SOFT mode for more forgiving timing

  fillWithRests(voice, measureNotes, totalTicks, stave, context);
}

async function playMeasures() {
  if (!synth || !audioInitialized) {
      console.log('Audio not initialized');
      return;
  }

  try {
      // Ensure audio context is in running state
      if (Tone.context.state !== 'running') {
          await Tone.context.resume();
      }

      isPlaying = true;
      const tempo = 120;
      const beatDuration = 60 / tempo;

      for (let measureIndex = 0; measureIndex < measures.length && isPlaying; measureIndex++) {
          const measure = measures[measureIndex];
          for (let noteIndex = 0; noteIndex < measure.length && isPlaying; noteIndex++) {
              const note = measure[noteIndex];
              if (!note.duration.includes("r")) {  // Skip rests
                  const noteKey = note.keys[0].split("/")[0];
                  const octave = note.keys[0].split("/")[1];
                  const frequency = NOTE_FREQUENCIES[noteKey.toLowerCase()] * 
                      Math.pow(2, octave - 4);

                  // Use Tone.js timing
                  synth.triggerAttackRelease(
                      frequency,
                      DURATIONS[note.duration].time,
                      Tone.now()
                  );
                  
                  // Wait for note duration
                  await new Promise(resolve => 
                      setTimeout(resolve, beatDuration * 1000 * DURATIONS[note.duration].beats)
                  );
              }
          }
      }
  } catch (error) {
      console.error('Playback error:', error);
      document.getElementById("error-message").textContent = 
          "Error during playback. Please try again.";
  } finally {
      isPlaying = false;
  }
}

// Create highlight elements
function createHighlightElements() {
  // Remove any existing highlights
  const existingHighlights = document.querySelectorAll('.staff-line-highlight, .staff-space-highlight');
  existingHighlights.forEach(el => el.remove());

  // Create staff line highlight
  staffLineHighlight = document.createElement('div');
  staffLineHighlight.className = 'staff-line-highlight';
  staffLineHighlight.style.display = 'none';
  document.querySelector('.staff-scroll-container').appendChild(staffLineHighlight);

  // Create staff space highlight
  staffSpaceHighlight = document.createElement('div');
  staffSpaceHighlight.className = 'staff-space-highlight';
  staffSpaceHighlight.style.display = 'none';
  document.querySelector('.staff-scroll-container').appendChild(staffSpaceHighlight);
}

// Add this function to handle note enabling/disabling
function updateSelectableNotes() {
    const { num, den } = getTimeSignature();
    const maxBeats = num * (4/den);  // Convert to quarter note beats

    // For each draggable note
    document.querySelectorAll('.draggable-note').forEach(note => {
        const duration = note.dataset.duration;
        const noteBeats = DURATIONS[duration]?.beats || 0;
        
        if (noteBeats > maxBeats) {
            // Disable the note
            note.classList.add('disabled-note');
            note.draggable = false;
        } else {
            // Enable the note
            note.classList.remove('disabled-note');
            note.draggable = true;
        }
    });
}

function handleDragStart(e) {
    if (e.target.classList.contains('disabled-note')) {
        e.preventDefault();
        return;
    }
    
  draggedDuration = e.target.dataset.duration;
  
  // Set drag image to be invisible
  const dragImage = document.createElement('div');
  dragImage.style.opacity = '0';
  document.body.appendChild(dragImage);
  e.dataTransfer.setDragImage(dragImage, 0, 0);
  
  setTimeout(() => dragImage.remove(), 0);
}

function handleDragEnd() {
  draggedDuration = null;
  staffLineHighlight.style.display = 'none';
  staffSpaceHighlight.style.display = 'none';

  const tooltip = document.querySelector('.position-tooltip');
  if (tooltip) tooltip.style.display = 'none';
}

function handleDragOver(e) {
  e.preventDefault();
  
  const staffContainer = e.currentTarget;
  const staffRect = staffContainer.getBoundingClientRect();
  const scrollLeft = staffContainer.scrollLeft;
  const scrollTop = staffContainer.scrollTop;
  
  // Calculate x and y relative to the container's viewport position
  const x = e.clientX - staffRect.left + scrollLeft;
  const y = e.clientY - staffRect.top + scrollTop;
  
  const rowHeight = 210;
  const currentRowIndex = Math.floor(y / rowHeight);
  const measureIndex = getMeasureIndexFromPosition(x, scrollLeft, currentRowIndex);
  
  // Calculate staff position
  const staffTop = 80 + (rowHeight * currentRowIndex);
  const staffLineSpacing = 5;
  const relativeY = y - staffTop;
  const lineIndex = Math.round(relativeY / staffLineSpacing);
  
  const clef = document.getElementById('clef-select').value;
  
  if (lineIndex >= -2 && lineIndex <= 10) {
      const positionInfo = getNoteNameFromPosition(lineIndex, clef);
      if (positionInfo) {
          // Calculate position for highlighting
          const snapPosition = staffTop + (lineIndex * staffLineSpacing);
          
          // Update visual feedback with absolute positioning
          if (positionInfo.type === 'line') {
              staffLineHighlight.style.display = 'block';
              staffLineHighlight.style.top = `${snapPosition}px`;
              staffSpaceHighlight.style.display = 'none';
          } else {
              staffSpaceHighlight.style.display = 'block';
              staffSpaceHighlight.style.top = `${snapPosition - staffLineSpacing/2}px`;
              staffLineHighlight.style.display = 'none';
          }
          
          // Update tooltip
          let tooltip = document.querySelector('.position-tooltip');
          if (!tooltip) {
              tooltip = document.createElement('div');
              tooltip.className = 'position-tooltip';
              document.body.appendChild(tooltip);
          }
          
          const noteName = positionInfo.note.split('/')[0].toUpperCase();
          const octave = positionInfo.note.split('/')[1];
          tooltip.textContent = `${noteName}${octave} (${positionInfo.type}, Measure ${measureIndex + 1})`;
          tooltip.style.left = `${e.pageX + 10}px`;
          tooltip.style.top = `${e.pageY + 10}px`;
          tooltip.style.display = 'block';
      }
  }
}

function handleDragLeave(e) {
  if (!e.currentTarget.contains(e.relatedTarget)) {
      staffLineHighlight.style.display = 'none';
      staffSpaceHighlight.style.display = 'none';
      
      const tooltip = document.querySelector('.position-tooltip');
      if (tooltip) {
          tooltip.style.display = 'none';
      }
  }
}

function handleDrop(e) {
  e.preventDefault();
  const duration = draggedDuration;
  
  const staffContainer = e.currentTarget;
  const staffRect = staffContainer.getBoundingClientRect();
  const scrollLeft = staffContainer.scrollLeft;
  const scrollTop = staffContainer.scrollTop;
  
  // Calculate x and y relative to the container's viewport position
  const x = e.clientX - staffRect.left + scrollLeft;
  const y = e.clientY - staffRect.top + scrollTop;
  
  const rowHeight = 210;
  const currentRowIndex = Math.floor(y / rowHeight);
  const measureIndex = getMeasureIndexFromPosition(x, scrollLeft, currentRowIndex);
  
  // Calculate staff position
  const staffTop = 80 + (rowHeight * currentRowIndex);
  const staffLineSpacing = 5;
  const relativeY = y - staffTop;
  const lineIndex = Math.round(relativeY / staffLineSpacing);
  
  if (lineIndex >= -2 && lineIndex <= 10) {
      addNote(duration, x, y, measureIndex);
  }
  
  // Clean up
  staffLineHighlight.style.display = 'none';
  staffSpaceHighlight.style.display = 'none';
  const tooltip = document.querySelector('.position-tooltip');
  if (tooltip) tooltip.style.display = 'none';
}

// Helper function to hide highlights and tooltip
function hideHighlightsAndTooltip(tooltip) {
  if (tooltip) tooltip.style.display = 'none';
  staffLineHighlight.style.display = 'none';
  staffSpaceHighlight.style.display = 'none';
}

// Event Listeners
document.getElementById('clef-select').addEventListener('change', function() {
    const confirmation = confirm("Sure to change clef? All the notes will be clear and cannot be undo.");
    if(confirmation){
        measures = [[]];
        currentMeasureIndex = 0;
        initializeStaves();
        triggerAutoSave();
        document.getElementById("error-message").textContent = "";
    }
});

document.getElementById('time-select').addEventListener('change', function() {
    const confirmation = confirm("Sure to change time signature? All the notes will be clear and cannot be undo.");
    if(confirmation){
        measures = [[]];
        currentMeasureIndex = 0;
        updateSelectableNotes();
        initializeStaves();
        triggerAutoSave();
        document.getElementById("error-message").textContent = "";
    }
});

document.getElementById("clear-notes").addEventListener("click", () => {
  const confirmation = confirm("Sure to clear all? This action cannot be undo.");

  if(confirmation){
    for(let i = 0; i < measures.length; i++){
      measures[i] = [];
    }
    initializeStaves();
    triggerAutoSave();
    document.getElementById("error-message").textContent = "";
  }
});

document.getElementById("play").addEventListener("click", async () => {
  try {
      // Always try to initialize audio on play click
      if (!audioInitialized) {
          const initialized = await initAudio();
          if (!initialized) {
              document.getElementById("error-message").textContent = 
                  "Please click play again to start audio playback";
              return;
          }
      }
      
      // Start playback only if initialization was successful
      if (audioInitialized) {
          document.getElementById("error-message").textContent = "";
          isPlaying = true;
          await playMeasures();
      }
  } catch (error) {
      console.error("Audio playback error:", error);
      document.getElementById("error-message").textContent = 
          "Error playing audio. Please try again.";
  }
});

document.getElementById("stop").addEventListener("click", () => {
  isPlaying = false;
  if (synth) {
      synth.triggerRelease();
  }
  document.getElementById("error-message").textContent = "";
});

document.getElementById("undo").addEventListener("click", () => history.undo());

document.getElementById("redo").addEventListener("click", () => history.redo());

document.addEventListener("keydown", (e) => {
  if (e.key === "Delete" || e.key === "Backspace") {
    if (selectedNote) {
      const noteElements = document.querySelectorAll(".vf-stavenote");
      const noteIndex = Array.from(noteElements).indexOf(selectedNote);
      if (noteIndex !== -1) {
        measures[currentMeasureIndex].splice(noteIndex, 1);
        selectedNote = null;
        initializeStaves();
      }
    }
  }
});

document.querySelectorAll(".draggable-note").forEach((note) => {
  note.addEventListener("dragstart", (e) => {
    e.dataTransfer.setData("text/plain", note.dataset.duration);
  });
});

document.querySelector(".staff-scroll-container").addEventListener("dragover", (e) => {
    e.preventDefault();
});

// Add scroll event listener to update highlight positions
document.querySelector('.staff-scroll-container').addEventListener('scroll', function(e) {
  if (staffLineHighlight.style.display === 'block' || staffSpaceHighlight.style.display === 'block') {
      // Trigger a dragover event to update positions
      const lastDragEvent = new MouseEvent('dragover', {
          clientX: parseInt(staffLineHighlight.style.left) || 0,
          clientY: parseInt(staffLineHighlight.style.top) || 0,
          bubbles: true
      });
      this.dispatchEvent(lastDragEvent);
  }
});

document.querySelectorAll('.accidental-btn').forEach(btn => {
  btn.addEventListener('click', function() {
      // Remove active class from all accidental buttons
      document.querySelectorAll('.accidental-btn').forEach(b => 
          b.classList.remove('active'));
      // Add active class to clicked button
      this.classList.add('active');
  });
});

document.querySelectorAll('.articulation-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        // Remove active class from all articulation buttons
        document.querySelectorAll('.articulation-btn').forEach(b => 
            b.classList.remove('active'));
        // Add active class to clicked button
        this.classList.add('active');
    });
});

document.getElementById('key-signature').addEventListener('change', function() {
  initializeStaves();
}, triggerAutoSave);

// Initialize everything when the page loads
document.addEventListener('DOMContentLoaded', function() {
  const sheetId = document.getElementById('sheet-editor').dataset.sheetId;
  
  // First initialize empty sheet
  measures = [[]];
  
  
  // Then load existing data
  fetch(`/api/load_sheet/${sheetId}/`)
      .then(response => response.json())
      .then(data => {
        // Set clef type 
        if (data.clefType) {
            document.getElementById('clef-select').value = data.clefType;
        }

        initializeStaves();
        initializePreviewSystem();

          if (data.measures && data.measures.length > 0) {
              // Set time signature
              if (data.timeSignature) {
                  document.getElementById('time-select').value = data.timeSignature;
              }
              updateSelectableNotes();
              
              // Set key signature
              if (data.keySignature) {
                  document.getElementById('key-signature').value = data.keySignature;
              }
              
              // Load measures
              measures = [];
              data.measures.forEach(measureData => {
                  const measure = [];
                  
                  // Add notes
                  measureData.notes.forEach(noteData => {
                      const note = new Vex.Flow.StaveNote({
                          keys: [noteData.pitch],
                          duration: noteData.duration,
                          auto_stem: true,
                          clef: data.clefType
                      });
                      
                      if (noteData.accidental) {
                          note.addAccidental(0, new Vex.Flow.Accidental(noteData.accidental));
                      }
                      if (noteData.articulation) {
                          note.addArticulation(0, new Vex.Flow.Articulation(noteData.articulation));
                      }
                      if (noteData.tie === 'start') {
                          note.tieStart = true;
                      } else if (noteData.tie === 'end') {
                          note.tied = true;
                      }
                      
                      measure.push(note);
                  });
                  
                  // Add rests
                  measureData.rests.forEach(restData => {
                      const rest = new Vex.Flow.StaveNote({
                          keys: ["b/4"],
                          duration: restData.duration + "r",
                          clef: data.clefType
                      });
                      measure.push(rest);
                  });
                  
                  measures.push(measure);
              });
              
              // Redraw the staves with loaded data
              initializeStaves();
          }
      })
      .catch(error => {
          console.error('Error loading sheet:', error);
      });
});