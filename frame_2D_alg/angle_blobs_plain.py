import numpy as np
from collections import deque
from frame_2D_alg import Classes
from frame_2D_alg.Classes import form_P
from frame_2D_alg.Classes import scan_P_
from frame_2D_alg.Classes import form_segment
from frame_2D_alg.Classes import form_blob
# Filters ------------------------------------------------------------------------
from frame_2D_alg.misc import get_filters
get_filters(globals())          # imports all filters at once
# --------------------------------------------------------------------------------
'''
    angle_blob is a component of intra_blob
'''
# ***************************************************** ANGLE BLOBS FUNCTIONS *******************************************
# Functions:
# -blob_to_ablobs()
# -get_angle()
# -comp_angle()
# ***********************************************************************************************************************

def blob_to_ablobs(blob):  # compute and compare angle, define ablobs, accumulate a, da, sda in all reps within gblob
    # same functionality as image_to_blobs() in frame_blobs.py

    frame = Classes.frame(blob.dert__, blob_rectangle=blob.blob_rectangle, num_params=9)
    # initialize frame object: initialize blob_ and params, assign dert__ and blob_rectangle, assign frame shape
    _P_ = deque()
    global y, Y, X
    Y, X = frame.dert__.shape
    a_ = get_angle(frame.dert__[0], frame.blob_rectangle[0])  # compute max gradient angles within gblob
    for y in range(Y - 1):
        a_, _P_ = comp_angle(a_, _P_, frame)  # vertical and lateral pixel comparison

    y = Y - 1   # frame ends, merge segs of last line into their blobs:
    while _P_:  form_blob(form_segment(_P_.popleft(), frame), frame)

    frame.terminate()  # delete frame.dert__ and frame.blob_rectangle
    blob.frame_ablobs = frame
    return frame
    # ---------- blob_to_ablobs() end -----------------------------------------------------------------------------------

def get_angle(dert_, P_map_, _P_map_ = False):  # default = False: no higher-line for first line
    " compute angle of gradient in and adjacent to selected gblob"
    a_ = np.full(P_map_.shape, -1)

    marg_angle_ = np.zeros(P_map_.shape, dtype=bool)           # to compute angle in blob-marginal derts
    marg_angle_[:-1] = np.logical_or(P_map_[:-1], P_map_[1:])  # derts right-adjacent to blob, for lower-line lateral comp
    marg_angle_ = np.logical_or(marg_angle_, _P_map_)          # derts down-adjacent to blob, for higher-line vertical comp

    dx_, dy_ = np.array([[dx, dy] for p, g, dx, dy in dert_]).T  # construct dx, dy array

    a_[marg_angle_] = np.arctan2(dy_[marg_angle_], dx_[marg_angle_]) * angle_coef + 128  # computes angle if marg_angle_== True
    return a_
    # ---------- compute_angle() end ------------------------------------------------------------------------------------

def comp_angle(a_, _P_, frame):
    " compare angle of adjacent pixels within frame == gblob "

    dert_, lower_dert_ = frame.dert__[y:y+2]
    P_map_, lower_P_map_ = frame.blob_rectangle[y:y+2]

    lower_a_ = get_angle(lower_dert_, P_map_, lower_P_map_)
    sda_ = np.abs(a_[1:] - a_[:-1]) + np.abs(lower_a_[:-1] - a_[:-1]) - 2 * ave

    P_ = deque()
    buff_ = deque()
    x = 0
    while x < X - 1:  # excludes last column
        while x < X - 1 and not P_map_[x]:
            x += 1
        if x < X - 1 and P_map_[x]:
            aP = Classes.P(y, x_1st=x, num_params=7)    # aP initialization
            while x < X - 1 and P_map_[x]:
                a = a_[x]
                sda = sda_[x]
                dert = dert_[x] + [a, sda]
                s = sda > 0
                aP = form_P(s, dert, x, aP, P_, buff_, _P_, frame)
                x += 1
            aP.terminate(x)  # aP' x_end
            scan_P_(aP, P_, buff_, _P_, frame)  # P scans hP_, constructing asegs and ablobs

    while buff_:
        seg = buff_.popleft()
        if seg.roots != 1:
            form_blob(seg, frame)
    while _P_:
        form_blob(form_segment(_P_.popleft(), frame), frame)
    return lower_a_, P_
    # ---------- comp_angle() end ------------------------------------------------------------------------------------

    # without Classes:

def comp_angle(blob, dert__):  # compute and compare angle, define ablobs, accumulate a, da, sda in all reps within gblob

    params, root_ = blob[2:4]
    root_ = sorted(root_, key=lambda segment: segment[1][2])  # sorted by min_y of a segment
    blob[4] = []    # ablob_
    params += [0, 0]  # += A, sDa
    global y
    y = blob[1][2]  # start from top line (pixel row) of the blob
    seg_ = []       # buffer of segments that contain y_line
    haP_ = deque()  # buffer of higher-line angle_Ps
    i = 0           # root_ index

    while y <= blob[1][3]:  # while y <= blob's max_y, buffer all y_line derts of a blob
        P_ = []
        while i < len(root_) and root_[i][1][2] == y:
            seg_.append([root_[i], 0])  # buffer y_line segs of a blob
            i += 1
        ii = 0
        while ii < len(seg_):
            seg, P = seg_[ii]        # P = Py_[ii][0] = seg[3][P][0]
            P_.append(seg[3][P][0])  # buffer y_line Ps of a blob
            if y == seg[1][3]:       # if y == max y of a segment
                seg_.pop(ii)         # remove from list
                ii -= 1
            else:
                P += 1
                seg_[ii][1] = P    # index of next-line P
            ii += 1
        P_ = sorted(P_, key = lambda P: P[1][0])    # sorted by min_x for scan_aP_()
        aP_ = deque()
        buff_ = deque()

        for P in P_:    # main operations:
            [min_x, max_x], L, dert_ = P[1], P[2][0], P[3]
            aP = [-1, [min_x, -1], [0, 0, 0, 0, 0, 0, 0], []]
            # lateral comp:
            dax_ = []
            _a = get_angle(dert_[0])    # compute or fetch angle of max gradient in dert quadrant
            for dert in dert_[1:]:
                a = get_angle(dert)
                dax_.append(abs(a - _a))  # compare angle to that of right-side quadrant
                _a = a
            if max_x == len(dert__[y]) - 2:
                dax_ += [ave]        # init lateral da with ave
            else:
                dax_ += [abs(get_angle(dert__[y][max_x + 1]) - _a) ]

            # vertical comp:
            if y == len(dert__) - 1:
                day_ = [ave] * L    # init vertical da_ with ave
            else:
                day_ = [abs(get_angle(dert) - get_angle(_dert)) for dert, _dert in zip(dert_, dert__[y + 1][min_x: max_x + 1])]
                # compare angles to those of same-x lower-line quadrants
            x = min_x
            for dert, dax, day in zip(dert_, dax_, day_):
                dert += [dax + day - 2 * ave]  # dert = p, g, dx, dy, a, sda: d_angle deviation, dx and dy for inc_range?
                aP = form_aP(dert, x, max_x, aP, aP_, buff_, haP_, blob)
                x += 1
                # ...to next dert/pixel in line...
            # ...to next P in line...

        while buff_:  # terminate remaining haPs
            haP = buff_.popleft()
            if haP[4] != 1: form_ablob(haP, blob)
        while haP_: form_ablob(form_asegment(haP_.popleft(), blob), blob)
        haP_ = aP_  # for next line
        y += 1
        # ...to next line...

    y = blob[1][3] + 1
    while haP_: form_ablob(form_asegment(haP_.popleft(), blob), blob)  # terminate Last row of haPs
    # ---------- comp_angle() end ---------------------------------------------------------------------------------------

def form_aP(dert, x, x_stop, aP, aP_, buff_, haP_, blob):
    p, g, dx, dy, a, sda = dert
    s = 1 if sda > 0 else 0
    pri_s = aP[0]

    if s != pri_s and pri_s != -1:  # aP is terminated:
        aP[1][1] = x - 1  # aP' max_x
        scan_aP_(aP, aP_, buff_, haP_, blob)  # aP scans haP_
        aP = [s, [x, -1], [0, 0, 0, 0, 0, 0, 0], []]  # new aP initialization

    [min_x, max_x], [L, I, G, Dx, Dy, A, sDa], dert_ = aP[1:]  # continued or initialized input and derivatives are accumulated:
    L += 1      # length of a pattern
    I += p      # summed input
    G += g      # summed gradient
    Dx += dx    # lateral D
    Dy += dy    # vertical D
    A += a      # summed angle
    sDa += sda  # summed deviation of difference in angle
    dert_.append(dert)  # derts are buffered for intra-blob()
    aP = [s, [min_x, max_x], [L, I, G, Dx, Dy, A, sDa], dert_]

    if x == x_stop:     # aP is terminated:
        aP[1][1] = x    # aP' max_x
        scan_aP_(aP, aP_, buff_, haP_, blob)
    return aP  # accumulated within line, P_ is a buffer for conversion to _P_
    # ---------- form_aP() end ------------------------------------------------------------------------------------------

def scan_aP_(aP, aP_, _buff_, haP_, blob):
    fork_ = []  # refs to haPs connected to input aP
    _min_x = 0  # to start while loop, next ini_x = _x + 1
    min_x, max_x = aP[1]

    while _min_x <= max_x:  # while x values overlap between aP and _aP
        if _buff_:
            haP = _buff_.popleft()  # haP was extended to segment and buffered in prior scan_aP_
        elif haP_:
            haP = form_asegment(haP_.popleft(), blob)
        else:
            break  # higher line ends, all haPs are converted to segments
        roots = haP[4]
        _aP = haP[3][-1][0]
        _min_x, _max_x = _aP[1]  # first_x, last_x

        if aP[0] == _aP[0] and min_x <= _max_x and _min_x <= max_x:
            roots += 1
            haP[4] = roots
            fork_.append(haP)   # aP-connected haPs will be converted to segments at each _fork
        if _max_x > max_x:      # x overlap between haP and next aP: haP is buffered for next scan_aP_, else haP included in a blob segment
            _buff_.append(haP)
        elif roots != 1:
            form_ablob(haP, blob)  # segment is terminated and packed into its blob
        _min_x = _max_x + 1     # = first x of next _aP

    aP_.append((aP, fork_))     # aP with no overlap to next _aP is extended to haP and buffered for next-line scan_aP_
    # ---------- scan_aP_() end -----------------------------------------------------------------------------------------

def form_asegment(haP, blob):
    _aP, fork_ = haP
    s, [min_x, max_x], params = _aP[:-1]
    ave_x = (params[0] - 1) // 2  # extra-x L = L-1 (1x in L)

    if not fork_:  # seg is initialized with initialized blob (params, coordinates, incomplete_segments, root_, xD)
        ablob = [s, [min_x, max_x, y - 1, -1, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0], [], 1]  # s, coords, params, root_, open_segments
        haP = [s, [min_x, max_x, y - 1, -1, 0, 0, ave_x], params, [(_aP, 0)], 0, fork_, ablob]
        ablob[3].append(haP)
    else:
        if len(fork_) == 1 and fork_[0][4] == 1:  # haP has one fork: haP[2][0], and that fork has one root: haP
            # haP is merged into higher-line blob segment (Pars, roots, _fork_, ave_x, xD, aPy_, blob) at haP[2][0]:
            fork = fork_[0]
            fork[1][0] = min(fork[1][0], min_x)
            fork[1][1] = max(fork[1][1], max_x)
            xd = ave_x - fork[1][5]
            fork[1][4] += xd
            fork[1][5] += abs(xd)
            fork[1][6] = ave_x
            L, I, G, Dx, Dy, A, sDa = params
            Ls, Is, Gs, Dxs, Dys, As, sDas = fork[2]  # seg params
            fork[2] = [Ls + L, Is + I, Gs + G, Dxs + Dx, Dys + Dy, As + A, sDas + sDa]
            fork[3].append((_aP, xd))  # aPy_: vertical buffer of aPs merged into seg
            fork[4] = 0  # reset roots
            haP = fork  # replace segment with including fork's segment
            ablob = haP[6]

        else:  # if >1 forks, or 1 fork that has >1 roots:
            haP = [s, [min_x, max_x, y - 1, -1, 0, 0, ave_x], params, [(_aP, 0)], 0, fork_, fork_[0][6]]  # seg is initialized with fork's blob
            ablob = haP[6]
            ablob[3].append(haP)  # segment is buffered into root_
            if len(fork_) > 1:  # merge blobs of all forks
                if fork_[0][4] == 1:  # if roots == 1
                    form_ablob(fork_[0], blob, 1)  # merge seg of 1st fork into its blob
                for fork in fork_[1:len(fork_)]:  # merge blobs of other forks into blob of 1st fork
                    if fork[4] == 1:
                        form_ablob(fork, blob, 1)
                    if not fork[6] is ablob:
                        [min_x, max_x, min_y, max_y, xD, abs_xD, Ly], [L, I, G, Dx, Dy, A, sDa], root_, open_segments = fork[6][1:]
                        ablob[1][0] = min(min_x, ablob[1][0])
                        ablob[1][1] = max(max_x, ablob[1][1])
                        ablob[1][2] = min(min_y, ablob[1][2])
                        ablob[1][4] += xD
                        ablob[1][5] += abs_xD
                        ablob[1][6] += Ly
                        ablob[2][0] += L
                        ablob[2][1] += I
                        ablob[2][2] += G
                        ablob[2][3] += Dx
                        ablob[2][4] += Dy
                        ablob[2][5] += A
                        ablob[2][6] += sDa
                        ablob[4] += open_segments
                        for seg in root_:
                            if not seg is fork:
                                seg[6] = ablob  # blobs in other forks are references to blob in the first fork
                                ablob[3].append(seg)  # buffer of merged root segments
                        fork[6] = ablob
                        ablob[3].append(fork)
                    ablob[4] -= 1
        ablob[1][0] = min(min_x, ablob[1][0])
        ablob[1][1] = max(max_x, ablob[1][1])
    return haP
    # ---------- form_asegment() end ------------------------------------------------------------------------------------

def form_ablob(term_seg, blob, y_carry=0):
    [min_x, max_x, min_y, max_y, xD, abs_xD, ave_x], [L, I, G, Dx, Dy, A, sDa], Py_, roots, fork_, ablob = term_seg[1:]
    ablob[1][4] += xD  # ave_x angle, to evaluate blob for re-orientation
    ablob[1][5] += len(Py_)  # Ly = number of slices in segment
    ablob[2][0] += L
    ablob[2][1] += I
    ablob[2][2] += G
    ablob[2][3] += Dx
    ablob[2][4] += Dy
    ablob[2][5] += A
    ablob[2][6] += sDa
    ablob[4] += roots - 1  # reference to term_seg is already in blob[9]
    term_seg[1][3] = y - 1 - y_carry  # y_carry: min elevation of term_seg over current hP

    if not ablob[4]:
        ablob[1][3] = term_seg[1][3]
        blob[2][5] += A    # params: A
        blob[2][6] += sDa  # params: sDa
        blob[4].append(ablob)
    # ---------- form_ablob() end ---------------------------------------------------------------------------------------

def get_angle(dert):
    " get angle of maximal gradient, or compute it if not available "
    if len(dert) == 4:
        dx, dy = dert[2:]
        dert += [int(math.atan2(dy, dx) * angle_coef) + 128]
    return dert[4]
    # ---------- get_angle() end ---------------------------------------------------------------------------------------