import collections
import multiprocessing
import time
import face_recognition

import cv2

if "forkserver" in multiprocessing.get_all_start_methods():
    # noinspection PyCallingNonCallable
    multiprocessing = multiprocessing.get_context("forkserver")

import queue
from socketIO_client import SocketIO, LoggingNamespace


# faces: (face_encodings, face_names)
# frame_queue: (id, frame)
# result_queue: (id, face_location, face_names)
def face_rec_processor(faces, frame_queue, result_queue):
    known_encodings, known_names = faces

    while True:
        try:
            frame_id, frame = frame_queue.get(block=False)
        except queue.Empty:
            time.sleep(0.05)
            continue

        # Find all the faces and face encodings in the current frame of video
        face_locations = face_recognition.face_locations(frame)
        face_encodings = face_recognition.face_encodings(frame, face_locations, num_jitters=2)

        face_names = []
        for face_encoding in face_encodings:
            # See if the face is a match for the known face(s)
            matches = face_recognition.compare_faces(known_encodings, face_encoding)
            name = "Unknown"

            # If a match was found in known_face_encodings, just use the first one.
            if True in matches:
                first_match_index = matches.index(True)
                name = known_names[first_match_index]

            face_names.append(name)

        try:
            result_queue.put((frame_id, face_locations, face_names), block=False)
        except queue.Full:
            pass


def camera_capture(frame_queue, frame_queue2):
    frame_id = 1
    video_capture = cv2.VideoCapture(0)

    try:
        while True:
            # Grab a single frame of video
            ret, frame = video_capture.read()

            # Resize frame of video to 1/4 size for faster face recognition processing
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

            # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
            rgb_small_frame = small_frame[:, :, ::-1]

            for f_queue, f_frame in [(frame_queue, rgb_small_frame), (frame_queue2, frame)]:
                try:
                    f_queue.get(block=False)
                except queue.Empty:
                    pass

                try:
                    f_queue.put((frame_id, f_frame), block=False)
                except queue.Full:
                    pass

            frame_id += 1
    finally:
        # Release handle to the webcam
        video_capture.release()


def main(socketIO):

    known_faces = [
        ('Barack Obama', 'obama.jpg'),
        ('Joe Biden', 'biden.jpg'),
        ('Will', 'will.jpg'),
        ('Boyd', 'boyd1.jpg'),
    ]

    known_face_names = [p[0] for p in known_faces]
    known_face_encodings = []

    for face_name, image_name in known_faces:
        print('Loading', face_name)
        # Load a sample picture and learn how to recognize it.
        image = face_recognition.load_image_file(image_name)
        image_face_locations = face_recognition.face_locations(image, number_of_times_to_upsample=2)
        image_encoding = face_recognition.face_encodings(image, image_face_locations, num_jitters=10)[0]
        known_face_encodings.append(image_encoding)

    print('Loaded faces')

    frame_queue = multiprocessing.Queue(8)  # used for frames sent for face recognition
    frame_queue2 = multiprocessing.Queue(8)  # used to pass frames from the camera to the display
    results_queue = multiprocessing.Queue(32)

    process_threads = [multiprocessing.Process(target=face_rec_processor, args=(
        (known_face_encodings, known_face_names),
        frame_queue,
        results_queue
    )) for _ in range(5)]

    for t in process_threads:
        t.start()

    camera_thread = multiprocessing.Process(target=camera_capture, args=(frame_queue, frame_queue2))
    camera_thread.start()

    # Initialize some variables
    face_locations = []
    face_names = []

    latest_result_frame_id = 0
    saved_image_num = 0

    # then we don't have to deal with the case where we try to find the most common of an empty list
    recent_names = [None]

    most_common_name = None

    try:
        while True:
            frame = None
            latest_frame_id = 0

            try:
                for _ in range(32):
                    result_id, r_face_locations, r_face_names = results_queue.get(block=False)
                    if result_id > latest_result_frame_id:
                        latest_result_frame_id = result_id
                        face_locations = r_face_locations
                        face_names = r_face_names
            except queue.Empty:
                pass

            try:
                for _ in range(32):
                    frame_id, r_frame = frame_queue2.get(block=False)
                    if frame_id > latest_frame_id:
                        latest_frame_id = frame_id
                        frame = r_frame
            except queue.Empty:
                pass

            if frame is None:
                time.sleep(0.01)
                continue

            if cv2.waitKey(1) & 0xFF == ord('s'):
                saved_image_num += 1
                cv2.imwrite('saved_image_{}.jpg'.format(saved_image_num), frame)

            recent_names.append(face_names[0] if face_names else None)
            if len(recent_names) > 20:
                del recent_names[0]

            name_counter = collections.Counter(recent_names)
            latest_common_name = name_counter.most_common(1)[0][0]

            if latest_common_name != most_common_name:
                most_common_name = latest_common_name
                socketIO.emit('user_detection', {'name': latest_common_name}, path='/relay')

            # Display the results
            for (top, right, bottom, left), name in zip(face_locations, face_names):
                # Scale back up face locations since the frame we detected in was scaled to 1/4 size
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4

                # Draw a box around the face
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

                # Draw a label with a name below the face
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

            prepped_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)

            # Display the resulting image
            cv2.imshow('Video', prepped_frame)

            # Hit 'q' on the keyboard to quit!
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        cv2.destroyAllWindows()
        try:
            camera_thread.terminate()
        except:
            pass
        for t in process_threads:
            try:
                t.terminate()
            except:
                pass


if __name__ == '__main__':
    print('Loading')
    with SocketIO('54.161.203.83', 80, LoggingNamespace) as socketIO:
        print('Acquired socket.io connection')
        # socketIO.emit('foo', 'some data', path='/relay')
        # socketIO.wait(seconds=1)
        main(socketIO)
