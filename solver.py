import heapq

# Check if a given puzzle is solveable
def is_solvable(puzzle_data: list[list[int]]):
  # Flatten the data and remove the blank
  flat = [item for row in puzzle_data for item in row]
  flat.remove(0)
  # Count the inversions
  inversions = 0
  for i in range(len(flat)):
    for j in range(i, len(flat)):
      if flat[j] < flat[i]:
        inversions += 1

  # If the width is odd, it's solvable if the inversions is even
  if len(puzzle_data[0]) % 2 == 1:
    return inversions % 2 == 0
  else:
    # Otherwise, find the row with the blank
    blankRow = -1
    for i in range(len(puzzle_data)):
      if puzzle_data[i].count(0) > 0:
        blankRow = i
        break
    # Add the distance from the bottom of the blank to the inversions
    # Then it's solvable if that value is even
    return (inversions + (len(puzzle_data) - blankRow - 1)) % 2 == 0

class State:
  flat: list[int]
  moveChar = ''
  _hash = 0
  _score = -1

  # When comparing for the open and closed lists,
  # we don't care which move we made specifically,
  # so just compare/hash the flat list
  def __hash__(self) -> int:
    if self._hash == 0:
      # Lists can't be hashed, but tuples can, so convert
      self._hash = hash(tuple(self.flat))
    return self._hash
  
  def __eq__(self, __value: object) -> bool:
    # This seems to be faster than checking is __value is a State
    # then comparing the flat lists
    # Since we know we only compare States to each other,
    # this won't cause false positives
    return hash(self) == hash(__value)

  def score(self, width: int) -> int:
    # We cache the score, so we only need to calculate it if we don't have it
    if self._score == -1:
      self._score = 0
      for i in range(len(self.flat)):
        # Don't count the blank spot
        if self.flat[i] == 0:
          continue
        # The wanted index is one less than the value,
        # since 1 wants to be at 0, etc.
        item = self.flat[i] - 1
        # Get the horizontal distance with mod
        self._score += abs((item % width) - (i % width))
        # Get the vertical distance with integer division
        self._score += abs((item // width) - (i // width))
    return self._score
  
  def move(self, char: str, x: int, y: int, dx: int, dy: int, width: int):
    # We need to keep track of the move we made for when we reconstruct the path
    self.moveChar = char
    # We're changing the flat list, so mark that we need to recache the hash
    self._hash = 0
    # x, y is the coords of the blank
    blankIdx = index(x, y, width)
    # Move by dx, dy from the blank to find the square we are moving
    x += dx
    y += dy
    # This is the index of the square we are moving
    i = index(x, y, width)
    # This is th enumber of the square we are moving
    item = self.flat[i]
    # If we subtract the score for the square we are moving in it's old position,
    # then add it's score for then new position, we've updated the score without needing to
    # go through the entire list
    self._score -= abs(((item - 1) % width) - (i % width))
    self._score -= abs(((item - 1) // width) - (i // width))
    self._score += abs(((item - 1) % width) - (blankIdx % width))
    self._score += abs(((item - 1) // width) - (blankIdx // width))
    # Actually swap the blank and the moving square
    self.flat[blankIdx] = item
    self.flat[i] = 0

# Make a state from the 2D puzzle data
# Really all we're doing is flattening it
def make_state(puzzle_data: list[list[int]]) -> State:
  state = State()
  state.flat = [item for row in puzzle_data for item in row]
  return state

# Clone a state, by copying the flat list, score, and hash
def clone(start: State) -> State:
  state = State()
  state.flat = start.flat.copy()
  state._score = start._score
  state._hash = start._hash
  return state

# Get the index of some coords in the flattened list
def index(x: int, y: int, width: int) -> int:
  return y * width + x

# Get the coords from an index
def from_index(idx: int, width: int):
  return idx % width, idx // width

# Calculate the list of moves from the end state and the closed list
def make_path(end: State, prev: State, closed_list: dict[State, State]) -> list[str]:
  path = []
  cur = prev
  # The closed list is a mapping of a state to the previous one,
  # so we can traverse it like this
  while cur in closed_list:
    path.append(cur.moveChar)
    cur = closed_list[cur]
  path.reverse()
  path.append(end.moveChar)
  # The initial state doesn't have a move,
  # but we don't want to include it anyway
  return path[1:]

# Get the info for adding a state to the open list
# This is the total score, the distance from the start,
# the iteration number, the state, and the previous state
# The order is important because tuple comparision compares them
# left to right
def info_for(active: State, prev: State, width: int, dist: int, i: int) -> tuple[int, int, State, State]:
  return (dist + 1 + active.score(width), dist + 1, i, active, prev)

# Solve a given puzzle
def solve(puzzle_data: list[list[int]]) -> list[str]:
  # Immediately return None if it's not solvable
  if not is_solvable(puzzle_data):
    return None
  
  # Determine the height and width
  height = len(puzzle_data)
  width = len(puzzle_data[0])
  # Make the initial state
  initial_state = make_state(puzzle_data)
  # Immediately return if we are given a finished puzzle
  if initial_state.score(width) == 0:
    return []
  
  # Iteration counter takes care of ties in the heap
  i = 0
  # Closed list is a mapping of a state to it's predecessor
  closed_list: dict[State, State] = dict()
  # Open list is a priority queue using heapq
  open_list: list[tuple[int, int, int, State, State]] = [(0, 0, i, initial_state, None)]

  while len(open_list) > 0:
    _, dist, _, active, prev = heapq.heappop(open_list)
    # If this state is already explored, skip it
    if active in closed_list:
      continue

    # If this state is the goal, return a path
    if active.score(width) == 0:
      return make_path(active, prev, closed_list)
    # Get the coords of the blank
    x, y = from_index(active.flat.index(0), width)

    # U move, only do it if the blank is not in the bottom row
    if y < height - 1:
      up = clone(active)
      # U move involves the tile below
      # (y starts at the top and increases downwards)
      up.move('U', x, y, 0, 1, width)
      if not up in closed_list:
        # We need to increment the iteration counter every time we add something to the queue
        i += 1
        heapq.heappush(open_list, info_for(up, active, width, dist, i))

    # D move, only do this if the blank is not in the top row
    if y > 0:
      down = clone(active)
      # D move involves the tile above
      # (y decreases upwards)
      down.move('D', x, y, 0, -1, width)
      if not down in closed_list:
        # We need to increment the iteration counter every time we add something to the queue
        i += 1
        heapq.heappush(open_list, info_for(down, active, width, dist, i))

    # L move, only do this if the blank is not in the rightmost row
    if x < width - 1:
      left = clone(active)
      # L move involves the tile to the right
      left.move('L', x, y, 1, 0, width)
      if not left in closed_list:
        # We need to increment the iteration counter every time we add something to the queue
        i += 1
        heapq.heappush(open_list, info_for(left, active, width, dist, i))

    # R move, only do this if the blank is not in the leftmost row
    if x > 0:
      right = clone(active)
      # R move invovles the tile to the left
      right.move('R', x, y, -1, 0, width)
      if not right in closed_list:
        # We need to increment the iteration counter every time we add something to the queue
        i += 1
        heapq.heappush(open_list, info_for(right, active, width, dist, i))

    # Finally, add the current state to the closed list
    closed_list[active] = prev

  # If we exhaust the open list without finding a solution, there isn't one
  return None
