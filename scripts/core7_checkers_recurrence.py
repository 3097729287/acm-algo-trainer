"""Check the actual cell cover, independently of any recursive tiling order."""
def tromino(inp,got,other=None):
    try:
        k,x,y=map(int,inp.split());n=2**k;data=list(map(int,got.split()))
        if len(data)!=(n*n-1):return False,'Wrong number of coordinates/orientations'
        # The cells extend from the corner in the two directions of the picture.
        offsets={1:[(0,0),(-1,0),(0,-1)],2:[(0,0),(-1,0),(0,1)],
                 3:[(0,0),(1,0),(0,-1)],4:[(0,0),(1,0),(0,1)]}
        occupied=bytearray(n*n);occupied[(x-1)*n+y-1]=1
        for at in range(0,len(data),3):
            row,column,shape=data[at:at+3]
            if shape not in offsets:return False,'Unknown orientation'
            for dx,dy in offsets[shape]:
                u,v=row+dx,column+dy
                if not (1<=u<=n and 1<=v<=n):return False,'Tile outside the board'
                index=(u-1)*n+v-1
                if occupied[index]:return False,'Overlap or princess cell covered'
                occupied[index]=1
        return all(occupied)
    except (ValueError,IndexError):return False,'Malformed tile output'
